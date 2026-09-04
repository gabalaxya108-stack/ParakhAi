from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import desc, func
from backend.app.db.session import SessionLocal
from backend.app.models import Inspection, Product, ComplianceCheck, Violation, Declaration
from backend.app.schemas.analytics import (
    RepeatedIssue,
    ManufacturerAnalyticsItem,
    ManufacturerAnalyticsResponse
)
from backend.app.core.logging import get_logger

logger = get_logger("services.analytics")

FIELD_LABELS = {
    "mrp": "Maximum Retail Price (MRP)",
    "net_quantity": "Net Quantity Declaration",
    "manufacturer": "Manufacturer Name & Address",
    "packer": "Packer Details",
    "importer": "Importer Details",
    "consumer_care": "Consumer Care Information",
    "manufacturing_date": "Date of Manufacture",
    "packing_date": "Date of Packaging",
    "country_of_origin": "Country of Origin",
    "batch_or_lot_number": "Batch / Lot Number",
    "product_name": "Common or Generic Name"
}

class ManufacturerAnalyticsService:
    """
    Aggregates historical inspection and compliance data at the manufacturer level.
    Adheres strictly to the principle of not declaring a manufacturer 'non-compliant'
    solely on the basis of preliminary AI screening.
    """

    @classmethod
    def get_manufacturer_analytics(
        cls,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        manufacturer_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        violation_type_filter: Optional[str] = None
    ) -> ManufacturerAnalyticsResponse:
        with SessionLocal() as db:
            query = db.query(Inspection)

            # Date range filtering
            if start_date:
                try:
                    s_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                    query = query.filter(Inspection.created_at >= s_dt)
                except Exception:
                    pass

            if end_date:
                try:
                    e_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    query = query.filter(Inspection.created_at <= e_dt)
                except Exception:
                    pass

            inspections = query.order_by(desc(Inspection.created_at)).all()

            # Grouping by manufacturer
            mfr_groups: Dict[str, Dict[str, Any]] = {}

            for insp in inspections:
                product = db.query(Product).filter(Product.id == insp.product_id).first() if insp.product_id else None

                # Category filter
                prod_cat = product.category if product else "packaged_commodity"
                if category_filter and category_filter != "ALL" and prod_cat.lower() != category_filter.lower():
                    continue

                mfr_name = (product.manufacturer if product and product.manufacturer else "").strip()
                if not mfr_name:
                    mfr_name = "Unspecified Commodity Manufacturer"

                # Manufacturer substring filter
                if manufacturer_filter and manufacturer_filter.strip():
                    if manufacturer_filter.lower().strip() not in mfr_name.lower():
                        continue

                # Query violations for this inspection
                viol_query = db.query(Violation).filter(Violation.inspection_id == insp.id)
                if violation_type_filter and violation_type_filter != "ALL":
                    viol_query = viol_query.filter(Violation.violation_type == violation_type_filter)
                violations = viol_query.all()

                # If violation filter was specified and inspection had none of that type, skip
                if violation_type_filter and violation_type_filter != "ALL" and not violations:
                    continue

                if mfr_name not in mfr_groups:
                    mfr_groups[mfr_name] = {
                        "name": mfr_name,
                        "inspections": [],
                        "violations": [],
                        "checks": [],
                        "latest_date": insp.created_at.isoformat()
                    }

                mfr_groups[mfr_name]["inspections"].append(insp)
                mfr_groups[mfr_name]["violations"].extend(violations)

                # Fetch compliance checks
                checks = db.query(ComplianceCheck).filter(ComplianceCheck.inspection_id == insp.id).all()
                mfr_groups[mfr_name]["checks"].extend(checks)

            # Build analytics items per manufacturer
            items: List[ManufacturerAnalyticsItem] = []
            total_potential_violations = 0
            total_repeated_issues_count = 0

            for mfr_name, data in mfr_groups.items():
                insps = data["inspections"]
                viols = data["violations"]
                checks = data["checks"]
                total = len(insps)

                compliant_cnt = sum(1 for i in insps if i.overall_status == "COMPLIANT")
                violations_cnt = sum(1 for i in insps if i.overall_status == "POTENTIAL_VIOLATION")
                review_cnt = sum(1 for i in insps if i.overall_status == "MANUAL_REVIEW")

                total_potential_violations += violations_cnt

                # Group repeated issues by field
                field_counter: Dict[str, Dict[str, Any]] = {}
                category_counter: Dict[str, int] = {}

                for v in viols:
                    f = v.field
                    field_counter[f] = field_counter.get(f, {"count": 0, "rule_id": v.rule_id, "type": v.violation_type})
                    field_counter[f]["count"] += 1

                    # Category counter (e.g. Mandatory Information, Pricing, Measurement)
                    cat_name = "Pricing & Taxes" if f == "mrp" else ("Measurement / Quantity" if f == "net_quantity" else "Manufacturer & Traceability")
                    category_counter[cat_name] = category_counter.get(cat_name, 0) + 1

                # Filter repeated issues list (sorted by highest frequency)
                repeated_list: List[RepeatedIssue] = []
                for f_key, f_info in sorted(field_counter.items(), key=lambda x: x[1]["count"], reverse=True):
                    repeated_list.append(
                        RepeatedIssue(
                            field=f_key,
                            label=FIELD_LABELS.get(f_key, f_key.replace("_", " ").title()),
                            count=f_info["count"],
                            rule_id=f_info["rule_id"],
                            violation_type=f_info["type"]
                        )
                    )
                    total_repeated_issues_count += f_info["count"]

                compliance_rate = round((compliant_cnt / total) * 100, 1) if total > 0 else 0.0
                avg_risk = round(sum(i.risk_score for i in insps) / total, 1) if total > 0 else 0.0

                # Statutory non-defamation wording:
                # Do not label a manufacturer "non-compliant" solely from AI screening results!
                if violations_cnt > 0:
                    status_label = "Repeated potential issues detected."
                elif review_cnt > 0:
                    status_label = "Manual inspection verification advised."
                else:
                    status_label = "No screening issues flagged."

                items.append(
                    ManufacturerAnalyticsItem(
                        manufacturer_name=mfr_name,
                        total_inspections=total,
                        compliant_inspections=compliant_cnt,
                        potential_violations=violations_cnt,
                        manual_reviews=review_cnt,
                        violation_categories=category_counter,
                        repeated_issues=repeated_list,
                        compliance_rate=compliance_rate,
                        average_risk=avg_risk,
                        status_label=status_label,
                        latest_inspection_date=data["latest_date"]
                    )
                )

            # Sort manufacturers with highest potential issues first
            items.sort(key=lambda x: (x.potential_violations, len(x.repeated_issues)), reverse=True)

            total_inspections_count = sum(item.total_inspections for item in items)

            return ManufacturerAnalyticsResponse(
                total_manufacturers=len(items),
                total_inspections=total_inspections_count,
                total_potential_violations=total_potential_violations,
                total_repeated_issues=total_repeated_issues_count,
                manufacturers=items
            )
