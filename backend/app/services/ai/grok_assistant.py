import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.repositories.regulatory_repository import RegulatoryRepository
from backend.app.repositories.inspection_repository import InspectionRepository

logger = get_logger("services.ai.niriksha_assistant")

def _strip_thinking_tags(text: str) -> str:
    """Strip Qwen-style <think>...</think> blocks from model output."""
    import re
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

class NirikshaAssistantService:
    """
    NIRIKSHA - PARAKH AI Conversational Regulatory Intelligence Assistant.
    Powered by Groq Ultra-Fast API (Qwen 3.8 27B / GPT-OSS 120B) with tool-assisted
    statutory grounding from the Legal Metrology database.
    Supports fluid multi-turn natural language dialogue with enforcement officers.
    """

    def __init__(self):
        # Prefer Groq for lightning-fast conversational experience
        self.groq_key = os.getenv("GROK_API_KEY", "") or os.getenv("GROQ_API_KEY", "") or getattr(settings, "GROK_API_KEY", "") or getattr(settings, "GROQ_API_KEY", "")
        self.groq_model = getattr(settings, "GROQ_CHAT_MODEL", "") or os.getenv("GROQ_CHAT_MODEL", "qwen/qwen3.8-27b")
        self.groq_endpoint = "https://api.groq.com/openai/v1/chat/completions"

        # Optional xAI Grok backup
        self.xai_key = os.getenv("XAI_API_KEY", "")
        self.xai_model = os.getenv("XAI_CHAT_MODEL", "grok-4.6")
        self.xai_endpoint = "https://api.x.ai/v1/chat/completions"

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes controlled platform database tools to retrieve authentic statutory data."""
        repo_reg = RegulatoryRepository()
        repo_insp = InspectionRepository()

        if tool_name == "get_inspection":
            insp_id = args.get("inspection_id", "")
            insp = repo_insp.get_inspection(insp_id)
            if not insp:
                return {"error": f"Inspection '{insp_id}' not found."}

            extracted_data = insp.get("extraction_result_json")
            if isinstance(extracted_data, str):
                try:
                    extracted_data = json.loads(extracted_data)
                except Exception:
                    extracted_data = {}

            fields = extracted_data.get("fields", {}) if isinstance(extracted_data, dict) else {}

            return {
                "inspection_id": insp.get("inspection_id"),
                "filename": insp.get("filename"),
                "created_at": insp.get("created_at"),
                "status": insp.get("status"),
                "product_name": fields.get("product_name", {}).get("value"),
                "mrp": fields.get("mrp", {}).get("value"),
                "net_quantity": fields.get("net_quantity", {}).get("value"),
                "manufacturer": fields.get("manufacturer", {}).get("value"),
                "mfg_date": fields.get("manufacturing_date", {}).get("value") or fields.get("packing_date", {}).get("value"),
                "consumer_care": fields.get("consumer_care", {}).get("value"),
                "country_of_origin": fields.get("country_of_origin", {}).get("value"),
                "batch_number": fields.get("batch_or_lot_number", {}).get("value"),
            }

        elif tool_name == "get_findings":
            insp_id = args.get("inspection_id", "")
            insp = repo_insp.get_inspection(insp_id)
            if not insp:
                return {"error": f"Findings for inspection '{insp_id}' unavailable."}
            comp = insp.get("compliance_result_json")
            if isinstance(comp, str):
                try:
                    comp = json.loads(comp)
                except Exception:
                    comp = {}
            if not isinstance(comp, dict):
                return {"error": f"Findings for inspection '{insp_id}' unavailable."}
            return {
                "inspection_id": insp_id,
                "overall_status": comp.get("overall_status"),
                "risk_score": comp.get("risk_score"),
                "violations": comp.get("violations", []),
                "checks": [
                    {
                        "rule_id": c.get("rule_id"),
                        "rule_title": c.get("rule_title"),
                        "status": c.get("status"),
                        "finding_reason": c.get("finding_reason")
                    }
                    for c in comp.get("checks", [])
                    if c.get("status") in ["POTENTIAL_VIOLATION", "MANUAL_REVIEW"]
                ],
                "total_checks_evaluated": len(comp.get("checks", []))
            }

        elif tool_name == "get_rule":
            rule_id = args.get("rule_id", "")
            rule = repo_reg.get_rule_by_id(rule_id)
            if not rule:
                return {"error": f"Statutory rule '{rule_id}' not found in database."}
            return rule.model_dump()

        elif tool_name == "search_rules":
            query = args.get("query", "").lower()
            rules = repo_reg.list_rules(status="ACTIVE")
            matched = [
                {
                    "rule_id": r.rule_id,
                    "section": r.section,
                    "sub_rule": r.sub_rule,
                    "title": r.title,
                    "requirement": r.requirement,
                    "severity": r.severity,
                    "source_excerpt": r.source_excerpt,
                    "source_url": r.source_url
                }
                for r in rules
                if query in r.rule_id.lower() or query in r.title.lower() or query in r.requirement.lower() or query in r.section.lower()
            ]
            return {"query": query, "matched_count": len(matched), "rules": matched[:6]}

        elif tool_name == "get_dashboard_metrics":
            summary = repo_reg.get_summary()
            inspections = repo_insp.list_inspections()
            potential_issues = sum(1 for i in inspections if isinstance(i.get("compliance_result_json"), dict) and i.get("compliance_result_json", {}).get("overall_status") == "POTENTIAL_VIOLATION")
            needs_review = sum(1 for i in inspections if isinstance(i.get("compliance_result_json"), dict) and i.get("compliance_result_json", {}).get("overall_status") == "MANUAL_REVIEW")
            return {
                "total_inspections": len(inspections),
                "potential_issues": potential_issues,
                "needs_review": needs_review,
                "active_rules": summary.active_rules,
                "total_documents": summary.documents_count
            }

        return {"error": f"Unknown platform tool '{tool_name}'."}

    def chat(
        self,
        user_query: str,
        context_inspection_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Conducts a conversational dialogue with the inspector using Groq.
        Fetches necessary database context and responds conversationally.
        """
        evidence_data: Dict[str, Any] = {}
        query_lower = user_query.lower()

        # Step 1: Detect and gather platform evidence based on context or query keywords
        import re
        extracted_insp_match = re.search(r"insp_[a-f0-9]+", user_query, re.IGNORECASE)
        active_insp_id = context_inspection_id or (extracted_insp_match.group(0) if extracted_insp_match else None)

        if active_insp_id:
            evidence_data["inspection"] = self.execute_tool("get_inspection", {"inspection_id": active_insp_id})
            evidence_data["findings"] = self.execute_tool("get_findings", {"inspection_id": active_insp_id})

        # Match statutory topics
        if any(w in query_lower for w in ["rule", "requirement", "amendment", "mrp", "price", "net", "quantity", "weight", "date", "mfg", "manufactur", "care", "consumer", "origin", "unit sale price", "usp"]):
            search_terms = []
            if "mrp" in query_lower or "price" in query_lower:
                search_terms.append("mrp")
            if "net" in query_lower or "quantity" in query_lower or "weight" in query_lower:
                search_terms.append("net")
            if "date" in query_lower or "mfg" in query_lower or "pack" in query_lower:
                search_terms.append("date")
            if "care" in query_lower or "consumer" in query_lower or "complaint" in query_lower:
                search_terms.append("care")
            if "usp" in query_lower or "unit sale" in query_lower:
                search_terms.append("unit sale")
            if "manufactur" in query_lower or "packer" in query_lower:
                search_terms.append("manufactur")

            kw = search_terms[0] if search_terms else "mandatory"
            evidence_data["rules"] = self.execute_tool("search_rules", {"query": kw})

        if any(w in query_lower for w in ["dashboard", "today", "summary", "stats", "metric", "overview", "total"]):
            evidence_data["dashboard_metrics"] = self.execute_tool("get_dashboard_metrics", {})

        # Step 2: Formulate Groq conversational request
        system_prompt = (
            "You are NIRIKSHA, the intelligent, conversational AI Regulatory Assistant on the PARAKH AI Legal Metrology Inspection Platform.\n"
            "You assist enforcement officers, inspectors, and regulatory authorities with package compliance reviews, statutory requirements, and legal metrology rules.\n\n"
            "CONVERSATIONAL STYLE & PERSONALITY:\n"
            "• Converse naturally, warmly, and authoritatively like an experienced Legal Metrology legal-technical advisor.\n"
            "• Be direct and concise. Structure your response with clean bullet points or bold text where appropriate so it is effortless to scan during an on-site inspection.\n"
            "• When an active package inspection is in context, directly explain the declarations found, violations flagged, and the specific statutory sections that apply.\n"
            "• If the package is compliant, confirm it clearly and explain which mandatory declarations satisfied the law.\n"
            "• If an issue is flagged (e.g. MRP missing 'incl. of all taxes', missing manufacturing date, missing consumer care, or no unit sale price), explain WHY it violated the rules and cite the exact Gazette/Rule clause.\n"
            "• Remind the user courteously when appropriate that this is AI-assisted advisory screening, and formal statutory enforcement remains under inspector authority.\n\n"
            f"CURRENT DATABASE EVIDENCE & GROUNDING:\n{json.dumps(evidence_data, indent=2, default=str)}"
        )

        # Build message history
        groq_messages = [{"role": "system", "content": system_prompt}]

        if history:
            # Filter and sanitize history turns
            for turn in history[-8:]:  # Keep last 8 turns for tight conversational context
                role = turn.get("role")
                content = turn.get("content")
                if role in ["user", "assistant"] and content:
                    groq_messages.append({"role": role, "content": content})

        groq_messages.append({"role": "user", "content": user_query})

        # Step 3: Execute conversational generation via Groq API
        if self.groq_key:
            for model_candidate in [self.groq_model, "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]:
                try:
                    payload = {
                        "model": model_candidate,
                        "messages": groq_messages,
                        "temperature": 0.4,
                        "max_tokens": 600
                    }
                    resp = requests.post(
                        self.groq_endpoint,
                        headers={
                            "Authorization": f"Bearer {self.groq_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        timeout=12.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        content = _strip_thinking_tags(data["choices"][0]["message"]["content"] or "")
                        if content and content.strip():
                            return {
                                "assistant_name": "NIRIKSHA",
                                "model": f"Groq • {model_candidate}",
                                "reply": content.strip(),
                                "evidence_used": evidence_data,
                                "status": "success"
                            }
                    else:
                        logger.warning(f"Groq model {model_candidate} returned status {resp.status_code}: {resp.text[:120]}")
                except Exception as e:
                    logger.warning(f"Groq API error on {model_candidate}: {e}")

        # Step 4: Fallback to xAI Grok if Groq was unavailable but XAI_API_KEY exists
        if self.xai_key:
            try:
                payload = {
                    "model": self.xai_model,
                    "messages": groq_messages,
                    "temperature": 0.3
                }
                resp = requests.post(
                    self.xai_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.xai_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = _strip_thinking_tags(data["choices"][0]["message"]["content"] or "")
                    return {
                        "assistant_name": "NIRIKSHA",
                        "model": f"xAI • {self.xai_model}",
                        "reply": content.strip(),
                        "evidence_used": evidence_data,
                        "status": "success"
                    }
            except Exception as e:
                logger.warning(f"xAI API error: {e}")

        # Step 5: Deterministic tool-grounded fallback
        reply_lines = []
        if "findings" in evidence_data and not evidence_data["findings"].get("error"):
            f = evidence_data["findings"]
            insp = evidence_data.get("inspection", {})
            prod_name = insp.get("product_name") or "Packaged Commodity"
            reply_lines.append(f"### Inspection Overview for **{prod_name}** (`{f['inspection_id']}`)")
            reply_lines.append(f"- **Screening Outcome**: `{f['overall_status']}` (Risk Score: {f['risk_score']})")

            violations = f.get("violations", [])
            if violations:
                reply_lines.append("\n#### Potential Regulatory Issues Detected:")
                for v in violations:
                    reply_lines.append(f"- **Rule `{v['rule_id']}`** ({v['field']}): {v['reason']}")
            else:
                reply_lines.append("\n✓ All mandatory statutory declarations (MRP, Net Quantity, Product Name, Date of Mfg, Consumer Care, Origin, Batch No) were verified and found **COMPLIANT**.")

        elif "rules" in evidence_data and not evidence_data["rules"].get("error"):
            r_list = evidence_data["rules"].get("rules", [])
            reply_lines.append("### Active Versioned Legal Metrology Rules")
            for r in r_list:
                reply_lines.append(f"- **Rule `{r['rule_id']}`** (Section `{r['section']}`): {r['requirement']}")
        else:
            reply_lines.append("Namaste Inspector. I am NIRIKSHA, your PARAKH AI Regulatory Assistant. How can I assist you with your Legal Metrology inspection today?")

        reply_lines.append("\n\n*Disclaimer: AI-assisted regulatory screening. Final enforcement determination remains with the competent inspector.*")

        return {
            "assistant_name": "NIRIKSHA",
            "model": "NIRIKSHA-Platform-Engine",
            "reply": "\n".join(reply_lines),
            "evidence_used": evidence_data,
            "status": "success"
        }
