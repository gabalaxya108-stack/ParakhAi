import os
import hashlib
import json
from datetime import datetime, timezone, timedelta
from backend.app.db.session import SessionLocal, engine
from backend.app.models import (
    User, Product, Inspection, Image, OCRResult,
    Declaration, ComplianceCheck, Violation, Evidence,
    InspectionReview, AuditLog, Complaint
)

def hash_password(password: str) -> str:
    # Deterministic salted SHA-256 for demo accounts
    return hashlib.sha256(f"parakh_salt_{password}".encode("utf-8")).hexdigest()

def seed_all():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1. Seed Demo Users
        users_to_seed = [
            {
                "username": "inspector.demo",
                "email": "inspector.demo@consumer.gov.in",
                "full_name": "Rajesh Sharma (Inspector ID: INS-DL-4029)",
                "role": "INSPECTOR",
                "password": "Parakh@123"
            },
            {
                "username": "officer.demo",
                "email": "officer.demo@consumer.gov.in",
                "full_name": "Dr. Meenakshi Sundaram (Deputy Controller)",
                "role": "OFFICER",
                "password": "Parakh@123"
            },
            {
                "username": "admin.demo",
                "email": "admin.demo@consumer.gov.in",
                "full_name": "National Informatics Centre Administrator",
                "role": "ADMIN",
                "password": "Parakh@123"
            },
            {
                "username": "supervisor.demo",
                "email": "supervisor.demo@consumer.gov.in",
                "full_name": "Suresh Raina (Chief Legal Metrology Officer)",
                "role": "SUPERVISOR",
                "password": "Parakh@123"
            }
        ]

        user_map = {}
        for u_data in users_to_seed:
            existing = db.query(User).filter(User.username == u_data["username"]).first()
            if not existing:
                u = User(
                    username=u_data["username"],
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    password_hash=hash_password(u_data["password"]),
                                        created_at=now
                )
                db.add(u)
                db.flush()
                user_map[u_data["username"]] = u
            else:
                user_map[u_data["username"]] = existing

        # 2. Seed Demo Products & Inspections
        demo_products = [
            {
                "insp_id": "insp_demo_compliant_01",
                "name": "Haldiram's Nagpur Moong Dal",
                "category": "food_packaged_commodity",
                "mfg": "Haldiram Snacks Pvt. Ltd., B-1/H-3, Mohan Co-op Industrial Estate, New Delhi 110044",
                "packer": "Haldiram Snacks Pvt. Ltd.",
                "importer": None,
                "origin": "India",
                "status": "EVALUATED",
                "overall_status": "COMPLIANT",
                "risk_score": 0,
                "review_status": "CLEARED",
                "declarations": {
                    "product_name": {"val": "Haldiram's Nagpur Moong Dal", "conf": 0.98, "bbox": {"x": 100, "y": 100, "width": 400, "height": 60}},
                    "mrp": {"val": "₹ 65.00 (Inclusive of all taxes)", "conf": 0.98, "bbox": {"x": 450, "y": 620, "width": 240, "height": 55}},
                    "net_quantity": {"val": "200 g", "conf": 0.97, "bbox": {"x": 120, "y": 710, "width": 160, "height": 50}},
                    "manufacturer": {"val": "Haldiram Snacks Pvt. Ltd., Mohan Co-op, New Delhi 110044", "conf": 0.96, "bbox": {"x": 80, "y": 800, "width": 400, "height": 90}},
                    "packer": {"val": "Haldiram Snacks Pvt. Ltd., Mohan Co-op, New Delhi 110044", "conf": 0.96, "bbox": {"x": 80, "y": 800, "width": 400, "height": 90}},
                    "manufacturing_date": {"val": "08/2026", "conf": 0.95, "bbox": {"x": 500, "y": 730, "width": 180, "height": 45}},
                    "packing_date": {"val": "08/2026", "conf": 0.95, "bbox": {"x": 500, "y": 730, "width": 180, "height": 45}},
                    "consumer_care": {"val": "care@haldirams.com / 1800-425-4444", "conf": 0.96, "bbox": {"x": 80, "y": 900, "width": 380, "height": 60}},
                    "country_of_origin": {"val": "India", "conf": 0.99, "bbox": {"x": 480, "y": 820, "width": 200, "height": 40}},
                    "batch_or_lot_number": {"val": "HD-26804", "conf": 0.95, "bbox": {"x": 500, "y": 770, "width": 170, "height": 40}}
                }
            },
            {
                "insp_id": "insp_demo_violation_02",
                "name": "Britannia Treat Vanilla Cream Biscuits",
                "category": "food_packaged_commodity",
                "mfg": None,  # Intentionally missing manufacturer address violation
                "packer": None,
                "importer": None,
                "origin": "India",
                "status": "EVALUATED",
                "overall_status": "NON_COMPLIANT",
                "risk_score": 75,
                "review_status": "PENDING",
                "declarations": {
                    "product_name": {"val": "Britannia Treat Vanilla Cream Biscuits", "conf": 0.96, "bbox": {"x": 100, "y": 100, "width": 400, "height": 60}},
                    "mrp": {"val": "₹ 30.00", "conf": 0.92, "bbox": {"x": 420, "y": 600, "width": 210, "height": 50}},
                    "net_quantity": {"val": "120 gms", "conf": 0.95, "bbox": {"x": 100, "y": 680, "width": 150, "height": 45}},
                    "manufacturing_date": {"val": "07/2026", "conf": 0.91, "bbox": {"x": 450, "y": 700, "width": 160, "height": 40}},
                    "consumer_care": {"val": "consumer@britannia.co.in", "conf": 0.88, "bbox": {"x": 90, "y": 840, "width": 320, "height": 50}},
                    "country_of_origin": {"val": "India", "conf": 0.95, "bbox": {"x": 450, "y": 780, "width": 160, "height": 35}}
                }
            },
            {
                "insp_id": "insp_demo_ambiguous_03",
                "name": "Bikaji Tana-Tan Mixture",
                "category": "food_packaged_commodity",
                "mfg": "Bikaji Foods International Ltd., F-196-199, Bichhwal Industrial Area, Bikaner, Rajasthan 334006",
                "packer": "Bikaji Foods International Ltd.",
                "importer": None,
                "origin": "India",
                "status": "EVALUATED",
                "overall_status": "NEEDS_REVIEW",
                "risk_score": 35,
                "review_status": "PENDING",
                "declarations": {
                    "product_name": {"val": "Bikaji Tana-Tan Mixture", "conf": 0.95, "bbox": {"x": 100, "y": 100, "width": 380, "height": 55}},
                    "mrp": {"val": "₹ 10.00 (Inclusive of all taxes)", "conf": 0.89, "bbox": {"x": 380, "y": 580, "width": 230, "height": 50}},
                    "net_quantity": {"val": "50 g", "conf": 0.91, "bbox": {"x": 110, "y": 650, "width": 140, "height": 45}},
                    "manufacturer": {"val": "Bikaji Foods, Bichhwal, Bikaner", "conf": 0.45, "bbox": {"x": 90, "y": 760, "width": 360, "height": 70}},
                    "manufacturing_date": {"val": "06/??", "conf": 0.42, "bbox": {"x": 420, "y": 720, "width": 140, "height": 35}}
                }
            }
        ]

        inspector_user = user_map.get("inspector.demo")

        for prod_data in demo_products:
            # Check or create product
            p = db.query(Product).filter(Product.product_name == prod_data["name"]).first()
            if not p:
                p = Product(
                    product_name=prod_data["name"],
                    category=prod_data["category"],
                    manufacturer=prod_data["mfg"],
                    packer=prod_data["packer"],
                    importer=prod_data["importer"],
                    country_of_origin=prod_data["origin"],
                    created_at=now - timedelta(days=2)
                )
                db.add(p)
                db.flush()

            # Check or create inspection
            insp = db.query(Inspection).filter(Inspection.inspection_id == prod_data["insp_id"]).first()
            if not insp:
                insp = Inspection(
                    inspection_id=prod_data["insp_id"],
                    product_id=p.id,
                    inspector_id=inspector_user.id if inspector_user else 1,
                    status=prod_data["status"],
                    overall_status=prod_data["overall_status"],
                    risk_score=prod_data["risk_score"],
                    review_status=prod_data["review_status"],
                    created_at=now - timedelta(hours=36),
                    updated_at=now - timedelta(hours=12)
                )
                db.add(insp)
                db.flush()

                # Image
                img = Image(
                    inspection_id=insp.id,
                    filename="display.jpg",
                    file_path="/uploads/sample.jpg",
                    file_size=204800,
                    mime_type="image/jpeg",
                    width=1200,
                    height=900,
                    created_at=now - timedelta(hours=36)
                )
                db.add(img)

                # Declarations
                for f_name, d_info in prod_data["declarations"].items():
                    decl = Declaration(
                        inspection_id=insp.id,
                        field_name=f_name,
                        extracted_value=d_info["val"],
                        confidence=d_info["conf"],
                        source="HYBRID_RECONCILER",
                        bounding_box=json.dumps(d_info["bbox"]) if d_info.get("bbox") else None,
                        created_at=now - timedelta(hours=35)
                    )
                    db.add(decl)

        db.commit()
        print("Database seeded successfully with users and demo inspections!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_all()
