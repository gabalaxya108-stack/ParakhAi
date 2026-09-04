import os
import uuid
from datetime import datetime
from fpdf import FPDF
from typing import Optional
from backend.app.core.config import settings
from backend.app.schemas.inspection import InspectionDetailResponse
from backend.app.schemas.rules import ComplianceStatus
from backend.app.services.cv_service import ComputerVisionService

class LegalMetrologyPDFReport(FPDF):
    def header(self):
        # Top government header
        self.set_fill_color(24, 43, 73) # Navy blue
        self.rect(0, 0, 210, 16, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.set_y(4)
        self.cell(0, 8, "GOVERNMENT OF INDIA - LEGAL METROLOGY ENFORCEMENT DIVISION", align="C")
        
        self.set_y(20)
        self.set_text_color(20, 30, 50)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 7, "PRELIMINARY COMPLIANCE INSPECTION & VIOLATION REPORT", ln=True, align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 110, 125)
        self.cell(0, 5, "Generated under Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011", ln=True, align="C")
        self.ln(3)
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-18)
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(130, 140, 150)
        self.cell(0, 4, "AI-Assisted Preliminary Compliance Screening Platform | Subject to Physical Officer Verification", ln=True, align="C")
        self.cell(0, 4, f"Page {self.page_no()} of {{nb}} | Official Legal Metrology Inspection Document", align="C")

class ReportService:
    @staticmethod
    def generate_inspection_pdf(inspection: InspectionDetailResponse) -> str:
        pdf = LegalMetrologyPDFReport(orientation="P", unit="mm", format="A4")
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=22)
        pdf.add_page()

        # 1. Metadata Grid
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(95, 6, f"Inspection Ref: {inspection.inspection_number}", ln=False)
        pdf.cell(95, 6, f"Date: {inspection.created_at[:19].replace('T', ' ')}", ln=True, align="R")

        pdf.set_font("Helvetica", "", 9)
        pdf.cell(95, 5, f"Commodity: {inspection.commodity_name}", ln=False)
        pdf.cell(95, 5, f"Category: {inspection.commodity_category}", ln=True, align="R")
        
        pdf.cell(95, 5, f"Brand: {inspection.brand_name or 'N/A'}", ln=False)
        pdf.cell(95, 5, f"Batch / Lot No: {inspection.batch_number or 'N/A'}", ln=True, align="R")

        pdf.cell(95, 5, f"PDP Surface Area: {inspection.pdp_area_sq_cm} sq cm", ln=False)
        pdf.cell(95, 5, f"Inspecting Officer: {inspection.inspector_name}", ln=True, align="R")
        pdf.ln(3)

        # 2. Executive Scorecard Banner
        is_compliant = (inspection.overall_compliance == ComplianceStatus.PASS)
        bg_color = (220, 252, 231) if is_compliant else (254, 226, 226)
        txt_color = (22, 101, 52) if is_compliant else (153, 27, 27)
        border_color = (134, 239, 172) if is_compliant else (248, 113, 113)

        pdf.set_fill_color(*bg_color)
        pdf.set_draw_color(*border_color)
        pdf.set_line_width(0.5)
        pdf.rect(14, pdf.get_y(), 182, 16, 'DF')
        
        pdf.set_y(pdf.get_y() + 2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*txt_color)
        verdict_text = "STATUS: FULLY COMPLIANT" if is_compliant else "STATUS: NON-COMPLIANCE / STATUTORY VIOLATIONS FLAGGED"
        pdf.cell(0, 6, verdict_text, ln=True, align="C")

        score = inspection.compliance_scorecard
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(0, 5, f"Total Rules: {score.total_rules}  |  Passed: {score.passed_count}  |  Violations: {score.failed_count}  |  Warnings: {score.warning_count}  |  Manual Check: {score.manual_check_count}", ln=True, align="C")
        pdf.ln(5)

        # 3. Itemized Rule Evaluation Table
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(30, 41, 59)
        pdf.set_draw_color(203, 213, 225)
        
        pdf.cell(24, 7, "Rule ID", 1, 0, 'C', True)
        pdf.cell(48, 7, "Legal Reference", 1, 0, 'L', True)
        pdf.cell(85, 7, "Findings / Statutory Verification", 1, 0, 'L', True)
        pdf.cell(25, 7, "Verdict", 1, 1, 'C', True)

        pdf.set_font("Helvetica", "", 7.5)
        for r in score.results:
            eff_status = r.override_verdict if r.inspector_override and r.override_verdict else r.status
            
            # Status colors
            if eff_status == ComplianceStatus.PASS:
                stat_color = (22, 101, 52)
                stat_text = "PASS"
            elif eff_status == ComplianceStatus.FAIL:
                stat_color = (185, 28, 28)
                stat_text = "VIOLATION"
            elif eff_status == ComplianceStatus.WARNING:
                stat_color = (180, 83, 9)
                stat_text = "WARNING"
            else:
                stat_color = (71, 85, 105)
                stat_text = "REVIEW"

            y_before = pdf.get_y()
            if y_before > 250:
                pdf.add_page()
                y_before = pdf.get_y()

            # Description snippet
            finding = r.violation_reason if eff_status == ComplianceStatus.FAIL and r.violation_reason else r.legal_citation
            if r.inspector_override:
                finding = f"[OVERRIDDEN by Officer: {r.override_reason}] " + finding

            # Clean cell text for PDF latin-1 safety
            clean_ref = r.legal_reference.encode('latin-1', 'replace').decode('latin-1')
            clean_finding = finding.encode('latin-1', 'replace').decode('latin-1')[:115]

            pdf.cell(24, 6.5, r.rule_id, 1, 0, 'C')
            pdf.cell(48, 6.5, clean_ref[:30], 1, 0, 'L')
            pdf.cell(85, 6.5, clean_finding, 1, 0, 'L')
            
            pdf.set_text_color(*stat_color)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.cell(25, 6.5, stat_text, 1, 1, 'C')
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(30, 41, 59)

        pdf.ln(4)

        # 4. Evidence Crops Section (Visual Bounding Boxes)
        violated_rules = [r for r in score.results if (r.override_verdict or r.status) == ComplianceStatus.FAIL and r.evidence_boxes]
        if violated_rules and inspection.image_url:
            raw_img_path = inspection.image_url.replace("/uploads/", "")
            full_img_path = os.path.join(settings.UPLOAD_DIR, raw_img_path)
            if not os.path.exists(full_img_path):
                # Fallback to fixtures directory
                full_img_path = os.path.join(settings.FIXTURES_DIR, os.path.basename(raw_img_path))

            if os.path.exists(full_img_path):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "STATUTORY EVIDENCE REGIONS (CROPPED FROM PACKAGING)", ln=True)
                pdf.ln(2)

                x_offset = 14
                y_offset = pdf.get_y()

                for idx, vr in enumerate(violated_rules[:3]):
                    box = vr.evidence_boxes[0]
                    crop_filename = f"crop_{inspection.id[:8]}_{idx}.jpg"
                    crop_path = os.path.join(settings.REPORT_DIR, crop_filename)
                    ComputerVisionService.crop_evidence_box(full_img_path, box, crop_path)

                    if os.path.exists(crop_path):
                        if pdf.get_y() > 220:
                            pdf.add_page()
                            y_offset = pdf.get_y()

                        pdf.image(crop_path, x=x_offset, y=pdf.get_y(), w=55, h=28)
                        pdf.set_y(pdf.get_y() + 29)
                        pdf.set_font("Helvetica", "B", 7)
                        pdf.set_text_color(185, 28, 28)
                        clean_ev_label = f"[{vr.rule_id}] {vr.rule_title[:24]}".encode('latin-1', 'replace').decode('latin-1')
                        pdf.cell(55, 4, clean_ev_label, ln=False, align="C")
                        x_offset += 62
                        pdf.set_y(pdf.get_y() - 29)

                pdf.ln(36)

        # 5. Inspector Sign-off & Statutory Notes
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, "INSPECTOR VERIFICATION & REMARKS:", ln=True)
        pdf.set_font("Helvetica", "", 8)
        notes = inspection.inspector_notes or "Inspection performed via AI-assisted computer vision screening. Verified against physical package declarations."
        clean_notes = notes.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4, clean_notes)
        pdf.ln(4)

        # Signature box
        pdf.line(130, pdf.get_y() + 10, 190, pdf.get_y() + 10)
        pdf.set_y(pdf.get_y() + 12)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(115, 4, "", ln=False)
        pdf.cell(75, 4, f"{inspection.inspector_name}", ln=True, align="C")
        pdf.set_font("Helvetica", "I", 7.5)
        pdf.cell(115, 4, "", ln=False)
        pdf.cell(75, 4, "Inspector, Legal Metrology", ln=True, align="C")

        # Output file
        output_filename = f"Notice_{inspection.inspection_number}_{inspection.id[:8]}.pdf"
        output_path = os.path.join(settings.REPORT_DIR, output_filename)
        pdf.output(output_path)
        return output_path
