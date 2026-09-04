import sqlite3
import json
from typing import Optional, List, Dict, Any
from backend.app.core.config import settings

class InspectionRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    inspection_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    image_location TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'UPLOADED',
                    ocr_result_json TEXT,
                    extraction_result_json TEXT,
                    compliance_result_json TEXT
                );
            """)
            cursor.execute("PRAGMA table_info(inspections);")
            columns = [row["name"] for row in cursor.fetchall()]
            if "ocr_result_json" not in columns:
                cursor.execute("ALTER TABLE inspections ADD COLUMN ocr_result_json TEXT;")
            if "extraction_result_json" not in columns:
                cursor.execute("ALTER TABLE inspections ADD COLUMN extraction_result_json TEXT;")
            if "compliance_result_json" not in columns:
                cursor.execute("ALTER TABLE inspections ADD COLUMN compliance_result_json TEXT;")
            conn.commit()

    def save_inspection(
        self,
        inspection_id: str,
        filename: str,
        mime_type: str,
        file_size: int,
        created_at: str,
        image_location: str,
        image_url: str,
        status: str = "UPLOADED"
    ) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inspections (
                    inspection_id, filename, mime_type, file_size,
                    created_at, image_location, image_url, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                inspection_id, filename, mime_type, file_size,
                created_at, image_location, image_url, status
            ))
            conn.commit()
            
        return {
            "inspection_id": inspection_id,
            "filename": filename,
            "mime_type": mime_type,
            "file_size": file_size,
            "created_at": created_at,
            "image_location": image_location,
            "image_url": image_url,
            "status": status
        }

    def get_inspection(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def list_inspections(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inspections ORDER BY created_at DESC")
            rows = cursor.fetchall()
            inspections_list = []
            for r in rows:
                item = dict(r)
                comp = json.loads(item["compliance_result_json"]) if item.get("compliance_result_json") else None
                ext = json.loads(item["extraction_result_json"]) if item.get("extraction_result_json") else None
                
                item["compliance_summary"] = {
                    "overall_status": comp.get("overall_status") if comp else "NOT_EVALUATED",
                    "risk_score": comp.get("risk_score", 0) if comp else 0,
                    "violations_count": len(comp.get("violations", [])) if comp else 0,
                    "product_category": comp.get("product_category", "packaged_commodity") if comp else "packaged_commodity",
                    "product_name": (
                        ext.get("fields", {}).get("product_name", {}).get("value")
                        if ext and isinstance(ext.get("fields"), dict)
                        else None
                    )
                }
                inspections_list.append(item)
            return inspections_list

    def save_ocr_result(self, inspection_id: str, ocr_result: dict) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inspections
                SET ocr_result_json = ?, status = 'OCR_COMPLETED'
                WHERE inspection_id = ?;
            """, (json.dumps(ocr_result), inspection_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_ocr_result(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ocr_result_json FROM inspections WHERE inspection_id = ?", (inspection_id,))
            row = cursor.fetchone()
            if not row or not row["ocr_result_json"]:
                return None
            return json.loads(row["ocr_result_json"])

    def save_extraction_result(self, inspection_id: str, extraction_result: dict) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inspections
                SET extraction_result_json = ?, status = 'EXTRACTION_COMPLETED'
                WHERE inspection_id = ?;
            """, (json.dumps(extraction_result), inspection_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_extraction_result(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT extraction_result_json FROM inspections WHERE inspection_id = ?", (inspection_id,))
            row = cursor.fetchone()
            if not row or not row["extraction_result_json"]:
                return None
            return json.loads(row["extraction_result_json"])

    def save_compliance_result(self, inspection_id: str, compliance_result: dict) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inspections
                SET compliance_result_json = ?, status = 'EVALUATED'
                WHERE inspection_id = ?;
            """, (json.dumps(compliance_result), inspection_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_review_status(self, inspection_id: str, status: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE inspections SET review_status = ? WHERE inspection_id = ?", (status, inspection_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_compliance_result(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT compliance_result_json FROM inspections WHERE inspection_id = ?", (inspection_id,))
            row = cursor.fetchone()
            if not row or not row["compliance_result_json"]:
                return None
            return json.loads(row["compliance_result_json"])

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Calculates real, authentic statistics directly from stored inspections.
        No fabricated or placeholder statistics.
        """
        inspections = self.list_inspections()
        total = len(inspections)
        compliant = 0
        violations = 0
        manual_review = 0
        pending = 0
        total_risk = 0
        evaluated_count = 0

        for insp in inspections:
            summary = insp.get("compliance_summary", {})
            st = summary.get("overall_status")
            if st == "COMPLIANT":
                compliant += 1
                total_risk += summary.get("risk_score", 0)
                evaluated_count += 1
            elif st == "POTENTIAL_VIOLATION":
                violations += 1
                total_risk += summary.get("risk_score", 0)
                evaluated_count += 1
            elif st == "MANUAL_REVIEW":
                manual_review += 1
                total_risk += summary.get("risk_score", 0)
                evaluated_count += 1
            else:
                pending += 1

        avg_risk = round(total_risk / evaluated_count, 1) if evaluated_count > 0 else 0.0

        return {
            "total_inspections": total,
            "compliant_count": compliant,
            "potential_violations_count": violations,
            "manual_review_count": manual_review,
            "pending_evaluation_count": pending,
            "average_risk_score": avg_risk,
            "recent_inspections": inspections[:6]
        }

_repository_instance = None

def get_inspection_repository() -> InspectionRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = InspectionRepository()
    return _repository_instance
