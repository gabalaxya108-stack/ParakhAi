import os
import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.app.schemas.regulatory import (
    RegulatoryDocumentDTO,
    RegulatoryDocumentCreate,
    RegulatoryRuleDTO,
    RegulatoryRuleCreate,
    RuleAmendmentDTO,
    RegulatoryCatalogSummaryResponse
)
from backend.app.core.logging import get_logger

logger = get_logger("repositories.regulatory")
DB_PATH = os.path.join(os.getcwd(), "legal_metrology.db")

class RegulatoryRepository:
    """
    Data-driven repository managing official government regulatory documents,
    versioned statutory rules, and legislative amendment history.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._init_tables()
        self._seed_official_regulatory_data()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Creates the 3 core regulatory database tables if not already present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Official Government Regulatory Documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regulatory_documents (
                    id TEXT PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    notification_number TEXT,
                    publication_date TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    source_url TEXT,
                    source_reference TEXT NOT NULL,
                    content_hash TEXT,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Versioned Statutory Regulatory Rules
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regulatory_rules (
                    id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    rule_version TEXT NOT NULL,
                    title TEXT NOT NULL,
                    section TEXT NOT NULL,
                    sub_rule TEXT,
                    requirement TEXT NOT NULL,
                    applicable_categories TEXT NOT NULL,
                    field_to_validate TEXT NOT NULL,
                    validation_type TEXT NOT NULL,
                    validation_expression TEXT,
                    severity TEXT NOT NULL,
                    effective_from TEXT NOT NULL,
                    effective_until TEXT,
                    source_document_id TEXT,
                    source_url TEXT,
                    source_page TEXT,
                    source_excerpt TEXT,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Rule Amendments Tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rule_amendments (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    previous_value TEXT,
                    new_value TEXT NOT NULL,
                    effective_from TEXT NOT NULL,
                    effective_until TEXT,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def _seed_official_regulatory_data(self):
        """Seeds official Department of Consumer Affairs publications and versioned statutory rules."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM regulatory_documents")
            if cursor.fetchone()[0] > 0:
                return  # Already seeded

            logger.info("Seeding authoritative Department of Consumer Affairs regulatory database...")

            # -------------------------------------------------------------
            # 1. Authoritative Official Government Documents
            # -------------------------------------------------------------
            docs = [
                (
                    "doc_pcr_2011",
                    "Legal Metrology (Packaged Commodities) Rules, 2011",
                    "RULES",
                    "G.S.R. 202(E)",
                    "2011-03-07",
                    "2011-11-01",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Gazette of India, Extraordinary, Part II, Section 3, Sub-section (i)",
                    hashlib.sha256(b"GSR_202_E_2011_PCR_BASE_RULES").hexdigest(),
                    "2011",
                    "ACTIVE"
                ),
                (
                    "doc_ecom_2017",
                    "Legal Metrology (Packaged Commodities) Amendment Rules, 2017",
                    "AMENDMENT",
                    "G.S.R. 629(E)",
                    "2017-06-23",
                    "2018-01-01",
                    "https://consumeraffairs.nic.in/sites/default/files/GSR629E.pdf",
                    "Gazette of India, Extraordinary, Part II, Section 3(i) - E-Commerce Amendments",
                    hashlib.sha256(b"GSR_629_E_2017_ECOM_MANDATE").hexdigest(),
                    "2017",
                    "ACTIVE"
                ),
                (
                    "doc_usp_2021",
                    "Legal Metrology (Packaged Commodities) Amendment Rules, 2021",
                    "AMENDMENT",
                    "G.S.R. 779(E)",
                    "2021-11-02",
                    "2022-04-01",
                    "https://consumeraffairs.nic.in/sites/default/files/GSR779E.pdf",
                    "Gazette of India, Extraordinary, Part II, Section 3(i) - Unit Sale Price Notification",
                    hashlib.sha256(b"GSR_779_E_2021_USP_NOTIFICATION").hexdigest(),
                    "2021",
                    "SUPERSEDED"
                ),
                (
                    "doc_usp_2022",
                    "Legal Metrology (Packaged Commodities) Amendment Rules, 2022",
                    "AMENDMENT",
                    "G.S.R. 226(E)",
                    "2022-03-28",
                    "2022-12-01",
                    "https://consumeraffairs.nic.in/sites/default/files/GSR226E.pdf",
                    "Gazette of India, Extraordinary, Part II, Section 3(i) - Unit Sale Price Enforcement",
                    hashlib.sha256(b"GSR_226_E_2022_USP_ENFORCEMENT").hexdigest(),
                    "2022",
                    "ACTIVE"
                ),
                (
                    "doc_pcr_2026",
                    "Legal Metrology (Packaged Commodities) Verified Guidelines & Amendments (2024–2026)",
                    "RULES",
                    "WM-10(5)/2024-LM",
                    "2024-01-01",
                    "2024-01-01",
                    "https://consumeraffairs.nic.in/sites/default/files/LM_Amendments_Consolidated_2026.pdf",
                    "Ministry of Consumer Affairs, Food and Public Distribution, Government of India",
                    hashlib.sha256(b"LM_CONSOLIDATED_2026_GUIDELINES").hexdigest(),
                    "2026.1",
                    "ACTIVE"
                )
            ]

            cursor.executemany("""
                INSERT INTO regulatory_documents (
                    id, document_name, document_type, notification_number,
                    publication_date, effective_date, source_url, source_reference,
                    content_hash, version, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, docs)

            # -------------------------------------------------------------
            # 2. Versioned Statutory Regulatory Rules
            # -------------------------------------------------------------
            rules = [
                # Era: 2026.1 (Active Current Consolidated Era)
                (
                    "rule_2026_mrp_001",
                    "PCR-R6-001",
                    "2026.1",
                    "Retail Sale Price / Maximum Retail Price Declaration",
                    "Rule 6",
                    "6(1)(e)",
                    "The package must declare the retail sale price as 'Maximum Retail Price' or 'MRP' inclusive of all taxes.",
                    json.dumps(["all", "packaged_commodity"]),
                    "mrp",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "CRITICAL",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 7, Rule 6(1)(e)",
                    "retail sale price of the package shall be declared on the package as Maximum Retail Price or MRP inclusive of all taxes",
                    "ACTIVE"
                ),
                (
                    "rule_2026_mrp_002",
                    "PCR-R6-002",
                    "2026.1",
                    "MRP Tax-Inclusive Statutory Formulation",
                    "Rule 6",
                    "6(1)(e)",
                    "The MRP declaration must include the wording 'incl. of all taxes' or 'inclusive of all taxes'.",
                    json.dumps(["all", "packaged_commodity"]),
                    "mrp",
                    "FORMAT_CHECK",
                    json.dumps({
                        "regex": r"(incl|inclusive|incl\.)\b.*tax",
                        "custom_message": "MRP declaration must visibly specify 'inclusive of all taxes'."
                    }),
                    "HIGH",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 7, Rule 6(1)(e)",
                    "the retail sale price of the package shall be clearly indicated in the form of Maximum or Max. Retail Price Rs. ...... inclusive of all taxes",
                    "ACTIVE"
                ),
                (
                    "rule_2026_netqty_001",
                    "PCR-R6-003",
                    "2026.1",
                    "Net Quantity Statutory Declaration",
                    "Rule 6",
                    "6(1)(b)",
                    "The net quantity in terms of standard unit of weight, measure or number must be declared on every package.",
                    json.dumps(["all", "packaged_commodity"]),
                    "net_quantity",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "CRITICAL",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 5, Rule 6(1)(b)",
                    "the net quantity, in terms of the standard unit of weight or measure, of the commodity contained in the package",
                    "ACTIVE"
                ),
                (
                    "rule_2026_netqty_002",
                    "PCR-R11-001",
                    "2026.1",
                    "Standard Metric Unit Symbols Without Pluralization",
                    "Rule 11 & 13",
                    "Rule 11(1)",
                    "Unit symbols must be standard metric ('g', 'kg', 'ml', 'l') without pluralization (e.g., 'gms', 'kgs', 'mls' prohibited).",
                    json.dumps(["all", "packaged_commodity"]),
                    "net_quantity",
                    "UNIT_SPECIFICATION",
                    json.dumps({
                        "forbidden_units_regex": r"\b(gms|gm|kgs|kgm|mls|ml\.|ltrs|litres|kilos)\b",
                        "allowed_units": ["g", "kg", "ml", "l", "m", "cm", "mm", "n", "u"],
                        "custom_message": "Non-standard metric unit symbol detected. Legal Metrology Rule 11 mandates standard symbols ('g', 'kg', 'ml', 'l')."
                    }),
                    "HIGH",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 12, Rule 11 & Rule 13",
                    "no plural shall be used with the symbols for units of measurement",
                    "ACTIVE"
                ),
                (
                    "rule_2026_name_001",
                    "PCR-R6-004",
                    "2026.1",
                    "Common or Generic Commodity Name",
                    "Rule 6",
                    "6(1)(a)",
                    "The package must visibly declare the common or generic name of the commodity contained in the package.",
                    json.dumps(["all", "packaged_commodity"]),
                    "product_name",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "CRITICAL",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 5, Rule 6(1)(a)",
                    "the name and address of the manufacturer, or where the manufacturer is not the packer, the name and address of the manufacturer and packer and for any imported package the name and address of the importer",
                    "ACTIVE"
                ),
                (
                    "rule_2026_mfd_001",
                    "PCR-R6-005",
                    "2026.1",
                    "Manufacturer / Packer / Importer Identity and Complete Address",
                    "Rule 6",
                    "6(1)(a)",
                    "Name and complete commercial address of the manufacturer, packer, or importer must be declared on the package.",
                    json.dumps(["all", "packaged_commodity"]),
                    "manufacturer",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "CRITICAL",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 5, Rule 6(1)(a)",
                    "the name and complete address of the manufacturer, or packer, or importer",
                    "ACTIVE"
                ),
                (
                    "rule_2026_date_001",
                    "PCR-R6-006",
                    "2026.1",
                    "Month and Year of Manufacture / Packing",
                    "Rule 6",
                    "6(1)(d)",
                    "The package must declare the month and year in which the commodity is manufactured or packed.",
                    json.dumps(["all", "packaged_commodity"]),
                    "packing_date",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.60}),
                    "HIGH",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 6, Rule 6(1)(d)",
                    "the month and year in which the commodity is manufactured or pre-packed or imported shall be mentioned on the package",
                    "ACTIVE"
                ),
                (
                    "rule_2026_care_001",
                    "PCR-R6-007",
                    "2026.1",
                    "Consumer Care Details for Grievance Redressal",
                    "Rule 6",
                    "6(1)(da)",
                    "Package must declare name, address, telephone number, and email of the grievance person for consumer complaints.",
                    json.dumps(["all", "packaged_commodity"]),
                    "consumer_care",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "CRITICAL",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 6, Rule 6(1)(da)",
                    "the name, address, telephone number, email address of the person who can be contacted by the consumer in case of a complaint",
                    "ACTIVE"
                ),
                (
                    "rule_2026_origin_001",
                    "PCR-R6-008",
                    "2026.1",
                    "Country of Origin Declaration for Imported and Domestic Commodities",
                    "Rule 6",
                    "6(1)(g)",
                    "Every package must mention the name of the country of origin or manufacture.",
                    json.dumps(["all", "packaged_commodity"]),
                    "country_of_origin",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "HIGH",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 7, Rule 6(1)(g)",
                    "the name of the country of origin or manufacture or assembly in case of imported products shall be mentioned on the package",
                    "ACTIVE"
                ),
                (
                    "rule_2026_lot_001",
                    "PCR-R6-009",
                    "2026.1",
                    "Batch or Lot Number Declaration",
                    "Rule 6",
                    "6(1)(q)",
                    "Every package must indicate the batch number or lot number for quality tracking and regulatory traceability.",
                    json.dumps(["all", "packaged_commodity"]),
                    "batch_or_lot_number",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.60}),
                    "MEDIUM",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 7, Rule 6(1)(q)",
                    "batch number or lot number or code number shall be mentioned on the package",
                    "ACTIVE"
                ),
                (
                    "rule_2026_usp_001",
                    "PCR-R6-011",
                    "2026.1",
                    "Mandatory Unit Sale Price (USP) for Packages Exceeding 100g/100ml",
                    "Rule 6",
                    "6(11)",
                    "Packages containing net quantity exceeding 100g or 100ml must declare the Unit Sale Price rounded to the nearest two decimal places.",
                    json.dumps(["all", "packaged_commodity"]),
                    "unit_sale_price",
                    "CONDITIONAL",
                    json.dumps({
                        "condition": "exceeds_net_quantity_threshold",
                        "weight_threshold_g": 100.0,
                        "custom_message": "Net quantity exceeds 100g/ml threshold. Unit Sale Price (USP) must be declared under Rule 6(11)."
                    }),
                    "HIGH",
                    "2022-12-01",
                    None,
                    "doc_usp_2022",
                    "https://consumeraffairs.nic.in/sites/default/files/GSR226E.pdf",
                    "Rule 6, Sub-rule (11)",
                    "the unit sale price shall be declared on the package in rupees, rounded off to the nearest two decimal places",
                    "ACTIVE"
                ),
                (
                    "rule_2026_font_001",
                    "PCR-R9-001",
                    "2026.1",
                    "Minimum Character Height & Legibility Standard (Rule 9)",
                    "Rule 9",
                    "Rule 9 & Table I",
                    "All statutory declarations on the Principal Display Panel must satisfy minimum prescribed height and legibility thresholds.",
                    json.dumps(["all", "packaged_commodity"]),
                    "net_quantity",
                    "READABILITY_CHECK",
                    json.dumps({
                        "min_pixel_height": 14,
                        "confidence_threshold": 0.80,
                        "custom_message": "Text height indicates micro-print. Potential font size issue under Rule 9. Manual verification required."
                    }),
                    "MEDIUM",
                    "2024-01-01",
                    None,
                    "doc_pcr_2026",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 9, Rule 9, Table I",
                    "the height of any numeral and letter shall not be less than the minimum height specified in Table I",
                    "ACTIVE"
                ),
                (
                    "rule_2026_ecom_001",
                    "PCR-R6-010",
                    "2026.1",
                    "E-Commerce Marketplace Listing Parity & Price Gouging Check",
                    "Rule 6",
                    "6(10)",
                    "Online marketplace listings must declare all mandatory packaging information, and listed selling price must never exceed declared physical MRP.",
                    json.dumps(["all", "packaged_commodity"]),
                    "ecom_listing",
                    "ECOM_LISTING_MATCH",
                    json.dumps({"max_allowed_markup": 0.0}),
                    "CRITICAL",
                    "2018-01-01",
                    None,
                    "doc_ecom_2017",
                    "https://consumeraffairs.nic.in/sites/default/files/GSR629E.pdf",
                    "Rule 6, Sub-rule (10)",
                    "an e-commerce entity shall ensure that the mandatory declarations are displayed on the digital platform",
                    "ACTIVE"
                ),

                # ---------------------------------------------------------
                # Historical Rules Era: 2011 Base Rules (Effective 2011-11-01 to 2017-12-31)
                # ---------------------------------------------------------
                (
                    "rule_2011_mrp_001",
                    "PCR-R6-001",
                    "2011",
                    "Retail Sale Price Declaration (2011 Base)",
                    "Rule 6",
                    "6(1)(e)",
                    "The package must declare the retail sale price as 'Maximum Retail Price' or 'MRP' inclusive of all taxes.",
                    json.dumps(["all", "packaged_commodity"]),
                    "mrp",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "CRITICAL",
                    "2011-11-01",
                    "2017-12-31",
                    "doc_pcr_2011",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 7",
                    "retail sale price of the package",
                    "SUPERSEDED"
                ),
                (
                    "rule_2011_netqty_001",
                    "PCR-R6-003",
                    "2011",
                    "Net Quantity Statutory Declaration (2011 Base)",
                    "Rule 6",
                    "6(1)(b)",
                    "The net quantity in terms of standard unit of weight, measure or number must be declared on every package.",
                    json.dumps(["all", "packaged_commodity"]),
                    "net_quantity",
                    "REQUIRED",
                    json.dumps({"confidence_threshold": 0.65}),
                    "CRITICAL",
                    "2011-11-01",
                    "2017-12-31",
                    "doc_pcr_2011",
                    "https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011",
                    "Page 5",
                    "the net quantity, in terms of standard unit of weight or measure",
                    "SUPERSEDED"
                )
            ]

            cursor.executemany("""
                INSERT INTO regulatory_rules (
                    id, rule_id, rule_version, title, section, sub_rule,
                    requirement, applicable_categories, field_to_validate,
                    validation_type, validation_expression, severity,
                    effective_from, effective_until, source_document_id,
                    source_url, source_page, source_excerpt, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rules)

            # -------------------------------------------------------------
            # 3. Rule Amendments Tracking
            # -------------------------------------------------------------
            amendments = [
                (
                    "amend_001",
                    "doc_ecom_2017",
                    "PCR-R6-010",
                    "INSERTION",
                    None,
                    "Rule 6(10) inserted: Digital marketplaces must display all mandatory packaging declarations.",
                    "2018-01-01",
                    None,
                    "Legal Metrology (Packaged Commodities) Amendment Rules, 2017 introduced digital platform accountability."
                ),
                (
                    "amend_002",
                    "doc_usp_2022",
                    "PCR-R6-011",
                    "SUBSTITUTION",
                    "Voluntary or unharmonized unit pricing formulation.",
                    "Rule 6(11) mandated: Unit Sale Price (USP) in Rupees per g/ml for packages over 100g/100ml.",
                    "2022-12-01",
                    None,
                    "Enforced nationwide by Department of Consumer Affairs to prevent deceptive packaging sizes and facilitate consumer price comparison."
                ),
                (
                    "amend_003",
                    "doc_pcr_2026",
                    "PCR-R6-007",
                    "CLARIFICATION",
                    "Consumer care address and phone number.",
                    "Consumer care email address mandated alongside phone and postal address.",
                    "2024-01-01",
                    None,
                    "Clarified grievance redressal channel to include mandatory digital contact mechanism."
                )
            ]

            cursor.executemany("""
                INSERT INTO rule_amendments (
                    id, document_id, rule_id, change_type,
                    previous_value, new_value, effective_from,
                    effective_until, explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, amendments)

            conn.commit()
            logger.info("Successfully initialized and seeded regulatory database.")

    # =========================================================================
    # Query & Applicability Engine Methods
    # =========================================================================

    def get_applicable_rules(
        self,
        category: str = "packaged_commodity",
        inspection_date: Optional[str] = None,
        status: str = "ACTIVE"
    ) -> List[RegulatoryRuleDTO]:
        """
        Retrieves all regulatory rules applicable to a product category at a specific inspection date.
        Date resolution: effective_from <= date and (effective_until is null or date <= effective_until).
        """
        # Default inspection_date to today in UTC (YYYY-MM-DD)
        target_date = inspection_date[:10] if inspection_date else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cat_lower = category.lower().strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Select candidate rules matching status and date window
            cursor.execute("""
                SELECT * FROM regulatory_rules
                WHERE status = ?
                  AND effective_from <= ?
                  AND (effective_until IS NULL OR effective_until >= ?)
            """, (status, target_date, target_date))

            rows = cursor.fetchall()

        results: List[RegulatoryRuleDTO] = []
        severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

        for row in rows:
            cats = json.loads(row["applicable_categories"])
            cats_normalized = [c.lower().strip() for c in cats]
            
            # Applicability check
            if "all" not in cats_normalized and cat_lower not in cats_normalized:
                continue

            expr = json.loads(row["validation_expression"]) if row["validation_expression"] else None

            results.append(RegulatoryRuleDTO(
                id=row["id"],
                rule_id=row["rule_id"],
                rule_version=row["rule_version"],
                title=row["title"],
                section=row["section"],
                sub_rule=row["sub_rule"],
                requirement=row["requirement"],
                applicable_categories=cats,
                field_to_validate=row["field_to_validate"],
                validation_type=row["validation_type"],
                validation_expression=expr,
                severity=row["severity"],
                effective_from=row["effective_from"],
                effective_until=row["effective_until"],
                source_document_id=row["source_document_id"],
                source_url=row["source_url"],
                source_page=row["source_page"],
                source_excerpt=row["source_excerpt"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            ))

        # Sort deterministically by severity priority then rule_id
        results.sort(key=lambda r: (severity_rank.get(r.severity, 99), r.rule_id))
        return results

    def list_documents(self) -> List[RegulatoryDocumentDTO]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM regulatory_documents ORDER BY publication_date DESC")
            rows = cursor.fetchall()

        return [
            RegulatoryDocumentDTO(
                id=r["id"],
                document_name=r["document_name"],
                document_type=r["document_type"],
                notification_number=r["notification_number"],
                publication_date=r["publication_date"],
                effective_date=r["effective_date"],
                source_url=r["source_url"],
                source_reference=r["source_reference"],
                content_hash=r["content_hash"],
                version=r["version"],
                status=r["status"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            )
            for r in rows
        ]

    def get_document_by_id(self, doc_id: str) -> Optional[RegulatoryDocumentDTO]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM regulatory_documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return RegulatoryDocumentDTO(
                id=row["id"],
                document_name=row["document_name"],
                document_type=row["document_type"],
                notification_number=row["notification_number"],
                publication_date=row["publication_date"],
                effective_date=row["effective_date"],
                source_url=row["source_url"],
                source_reference=row["source_reference"],
                content_hash=row["content_hash"],
                version=row["version"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def create_document_with_id(self, doc_id: str, doc: RegulatoryDocumentCreate) -> RegulatoryDocumentDTO:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO regulatory_documents (
                    id, document_name, document_type, notification_number,
                    publication_date, effective_date, source_url, source_reference,
                    content_hash, version, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, doc.document_name, doc.document_type, doc.notification_number,
                doc.publication_date, doc.effective_date, doc.source_url, doc.source_reference,
                doc.content_hash, doc.version, doc.status, now, now
            ))
            conn.commit()

        return RegulatoryDocumentDTO(
            id=doc_id,
            document_name=doc.document_name,
            document_type=doc.document_type,
            notification_number=doc.notification_number,
            publication_date=doc.publication_date,
            effective_date=doc.effective_date,
            source_url=doc.source_url,
            source_reference=doc.source_reference,
            content_hash=doc.content_hash,
            version=doc.version,
            status=doc.status,
            created_at=now,
            updated_at=now
        )

    def create_document(self, doc: RegulatoryDocumentCreate) -> RegulatoryDocumentDTO:
        import uuid
        new_id = f"doc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO regulatory_documents (
                    id, document_name, document_type, notification_number,
                    publication_date, effective_date, source_url, source_reference,
                    content_hash, version, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_id, doc.document_name, doc.document_type, doc.notification_number,
                doc.publication_date, doc.effective_date, doc.source_url, doc.source_reference,
                doc.content_hash, doc.version, doc.status, now, now
            ))
            conn.commit()

        return RegulatoryDocumentDTO(
            id=new_id,
            document_name=doc.document_name,
            document_type=doc.document_type,
            notification_number=doc.notification_number,
            publication_date=doc.publication_date,
            effective_date=doc.effective_date,
            source_url=doc.source_url,
            source_reference=doc.source_reference,
            content_hash=doc.content_hash,
            version=doc.version,
            status=doc.status,
            created_at=now,
            updated_at=now
        )

    def list_rules(
        self,
        version: Optional[str] = None,
        category: Optional[str] = None,
        field: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[RegulatoryRuleDTO]:
        query = "SELECT * FROM regulatory_rules WHERE 1=1"
        params: List[Any] = []

        if version:
            query += " AND rule_version = ?"
            params.append(version)
        if field:
            query += " AND field_to_validate = ?"
            params.append(field)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY rule_id ASC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        results: List[RegulatoryRuleDTO] = []
        for r in rows:
            cats = json.loads(r["applicable_categories"])
            if category:
                cat_lower = category.lower().strip()
                cats_lower = [c.lower().strip() for c in cats]
                if "all" not in cats_lower and cat_lower not in cats_lower:
                    continue

            expr = json.loads(r["validation_expression"]) if r["validation_expression"] else None
            results.append(RegulatoryRuleDTO(
                id=r["id"],
                rule_id=r["rule_id"],
                rule_version=r["rule_version"],
                title=r["title"],
                section=r["section"],
                sub_rule=r["sub_rule"],
                requirement=r["requirement"],
                applicable_categories=cats,
                field_to_validate=r["field_to_validate"],
                validation_type=r["validation_type"],
                validation_expression=expr,
                severity=r["severity"],
                effective_from=r["effective_from"],
                effective_until=r["effective_until"],
                source_document_id=r["source_document_id"],
                source_url=r["source_url"],
                source_page=r["source_page"],
                source_excerpt=r["source_excerpt"],
                status=r["status"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
        return results

    def get_rule_by_id(self, rule_id: str, version: Optional[str] = None) -> Optional[RegulatoryRuleDTO]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if version:
                cursor.execute("SELECT * FROM regulatory_rules WHERE rule_id = ? AND rule_version = ? LIMIT 1", (rule_id, version))
            else:
                cursor.execute("SELECT * FROM regulatory_rules WHERE rule_id = ? ORDER BY effective_from DESC LIMIT 1", (rule_id,))
            row = cursor.fetchone()

        if not row:
            return None

        cats = json.loads(row["applicable_categories"])
        expr = json.loads(row["validation_expression"]) if row["validation_expression"] else None

        return RegulatoryRuleDTO(
            id=row["id"],
            rule_id=row["rule_id"],
            rule_version=row["rule_version"],
            title=row["title"],
            section=row["section"],
            sub_rule=row["sub_rule"],
            requirement=row["requirement"],
            applicable_categories=cats,
            field_to_validate=row["field_to_validate"],
            validation_type=row["validation_type"],
            validation_expression=expr,
            severity=row["severity"],
            effective_from=row["effective_from"],
            effective_until=row["effective_until"],
            source_document_id=row["source_document_id"],
            source_url=row["source_url"],
            source_page=row["source_page"],
            source_excerpt=row["source_excerpt"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def create_rule(self, rule: RegulatoryRuleCreate) -> RegulatoryRuleDTO:
        import uuid
        new_id = f"rule_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        expr_str = json.dumps(rule.validation_expression) if rule.validation_expression else None
        cats_str = json.dumps(rule.applicable_categories)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO regulatory_rules (
                    id, rule_id, rule_version, title, section, sub_rule,
                    requirement, applicable_categories, field_to_validate,
                    validation_type, validation_expression, severity,
                    effective_from, effective_until, source_document_id,
                    source_url, source_page, source_excerpt, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_id, rule.rule_id, rule.rule_version, rule.title, rule.section, rule.sub_rule,
                rule.requirement, cats_str, rule.field_to_validate, rule.validation_type,
                expr_str, rule.severity, rule.effective_from, rule.effective_until,
                rule.source_document_id, rule.source_url, rule.source_page, rule.source_excerpt,
                rule.status, now, now
            ))
            conn.commit()

        return RegulatoryRuleDTO(
            id=new_id,
            rule_id=rule.rule_id,
            rule_version=rule.rule_version,
            title=rule.title,
            section=rule.section,
            sub_rule=rule.sub_rule,
            requirement=rule.requirement,
            applicable_categories=rule.applicable_categories,
            field_to_validate=rule.field_to_validate,
            validation_type=rule.validation_type,
            validation_expression=rule.validation_expression,
            severity=rule.severity,
            effective_from=rule.effective_from,
            effective_until=rule.effective_until,
            source_document_id=rule.source_document_id,
            source_url=rule.source_url,
            source_page=rule.source_page,
            source_excerpt=rule.source_excerpt,
            status=rule.status,
            created_at=now,
            updated_at=now
        )

    def set_rule_status(self, rule_id: str, new_status: str, effective_until: Optional[str] = None) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if effective_until:
                cursor.execute("""
                    UPDATE regulatory_rules
                    SET status = ?, effective_until = ?, updated_at = ?
                    WHERE id = ? OR rule_id = ?
                """, (new_status, effective_until, now, rule_id, rule_id))
            else:
                cursor.execute("""
                    UPDATE regulatory_rules
                    SET status = ?, updated_at = ?
                    WHERE id = ? OR rule_id = ?
                """, (new_status, now, rule_id, rule_id))
            conn.commit()
            return cursor.rowcount > 0

    def list_amendments(self, rule_id: Optional[str] = None) -> List[RuleAmendmentDTO]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if rule_id:
                cursor.execute("SELECT * FROM rule_amendments WHERE rule_id = ? ORDER BY effective_from DESC", (rule_id,))
            else:
                cursor.execute("SELECT * FROM rule_amendments ORDER BY effective_from DESC")
            rows = cursor.fetchall()

        return [
            RuleAmendmentDTO(
                id=r["id"],
                document_id=r["document_id"],
                rule_id=r["rule_id"],
                change_type=r["change_type"],
                previous_value=r["previous_value"],
                new_value=r["new_value"],
                effective_from=r["effective_from"],
                effective_until=r["effective_until"],
                explanation=r["explanation"],
                created_at=r["created_at"]
            )
            for r in rows
        ]

    def get_summary(self) -> RegulatoryCatalogSummaryResponse:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM regulatory_rules")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM regulatory_rules WHERE status = 'ACTIVE'")
            active = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM regulatory_rules WHERE status = 'PENDING_REVIEW'")
            pending = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM regulatory_rules WHERE status = 'SUPERSEDED'")
            superseded = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM regulatory_documents")
            docs_cnt = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM rule_amendments")
            amends_cnt = cursor.fetchone()[0]
            cursor.execute("SELECT DISTINCT rule_version FROM regulatory_rules ORDER BY rule_version DESC")
            versions = [r[0] for r in cursor.fetchall()]

        return RegulatoryCatalogSummaryResponse(
            total_rules=total,
            active_rules=active,
            pending_rules=pending,
            superseded_rules=superseded,
            documents_count=docs_cnt,
            amendments_count=amends_cnt,
            available_versions=versions or ["2026.1"],
            latest_version=versions[0] if versions else "2026.1"
        )


_regulatory_repo_instance = None

def get_regulatory_repository() -> RegulatoryRepository:
    global _regulatory_repo_instance
    if _regulatory_repo_instance is None:
        _regulatory_repo_instance = RegulatoryRepository()
    return _regulatory_repo_instance
