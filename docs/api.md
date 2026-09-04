# API Specification (v1)

## Base URL
All v1 API endpoints are prefixed with:
```
/api/v1
```

## Endpoints

### 1. Health Check
- **Route**: `GET /api/v1/health`
- **Description**: Returns operational status, environment name, version, and server uptime.
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "Legal Metrology Compliance Platform",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-09-03T13:51:00.123456+00:00",
  "uptime_seconds": 45.2
}
```

### 2. Root Service Greeting
- **Route**: `GET /`
- **Response**: `200 OK`
```json
{
  "message": "Welcome to Legal Metrology Compliance Platform API",
  "version": "1.0.0",
  "docs_url": "/api/v1/docs",
  "health_url": "/api/v1/health"
}
```

## Interactive Documentation
When running locally:
- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/openapi.json`

### 3. Upload Package Image
- **Route**: `POST /api/v1/inspections`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: File (JPG, PNG, TIFF up to 15MB)
- **Response**: `201 Created`
```json
{
  "inspection_id": "insp_d1026ca5708d",
  "filename": "test_package_label.jpg",
  "mime_type": "image/jpeg",
  "file_size": 4429,
  "created_at": "2026-09-03T14:06:44.821948+00:00",
  "image_location": "insp_d1026ca5708d/original.jpg",
  "image_url": "/uploads/insp_d1026ca5708d/original.jpg",
  "status": "UPLOADED"
}
```

### 4. Retrieve Inspection
- **Route**: `GET /api/v1/inspections/{inspection_id}`
- **Response**: `200 OK`
```json
{
  "inspection_id": "insp_d1026ca5708d",
  "filename": "test_package_label.jpg",
  "mime_type": "image/jpeg",
  "file_size": 4429,
  "created_at": "2026-09-03T14:06:44.821948+00:00",
  "image_location": "insp_d1026ca5708d/original.jpg",
  "image_url": "/uploads/insp_d1026ca5708d/original.jpg",
  "status": "UPLOADED"
}
```

### 5. Extract Text via OCR Service
- **Route**: `POST /api/v1/inspections/{inspection_id}/ocr`
- **Description**: Invokes the decoupled OCR Provider abstraction (mock, tesseract, azure_vision) to detect and extract all text tokens, confidence ratings, and bounding boxes.
- **Response**: `200 OK`
```json
{
  "inspection_id": "insp_fe92dd841074",
  "full_text": "CRUNCHY MAGIC MASALA POTATO CHIPS\nPOTATO CHIPS\nNet Wt.: 120 gms\nMRP ₹40\n...",
  "blocks": [
    {
      "text": "MRP ₹40",
      "confidence": 0.97,
      "bounding_box": {
        "x": 112,
        "y": 864,
        "width": 248,
        "height": 60
      },
      "normalized_box": {
        "ymin": 0.72,
        "xmin": 0.14,
        "ymax": 0.77,
        "xmax": 0.45
      },
      "page_number": 1
    }
  ],
  "total_blocks": 9,
  "image_width": 800,
  "image_height": 1200,
  "provider": "mock",
  "processing_time_ms": 11.13
}
```

### 6. Retrieve Cached OCR Results
- **Route**: `GET /api/v1/inspections/{inspection_id}/ocr`
- **Description**: Returns previously computed OCR extraction for an inspection.
- **Response**: `200 OK` (or `404 Not Found` if OCR has not been triggered yet)

### 7. Extract Mandatory Legal Declarations
- **Route**: `POST /api/v1/inspections/{inspection_id}/extract`
- **Description**: Invokes the AI perception extraction service to locate the 11 mandatory declaration fields (`product_name`, `manufacturer`, `packer`, `importer`, `net_quantity`, `mrp`, `packing_date`, `manufacturing_date`, `consumer_care`, `country_of_origin`, `batch_or_lot_number`) and their bounding boxes. Strictly validates model output. Missing fields are strictly set to `null` without hallucination. Does NOT determine legal compliance.
- **Response**: `200 OK`
```json
{
  "inspection_id": "insp_05242eabf637",
  "fields": {
    "product_name": {
      "field": "product_name",
      "value": "CRUNCHY MAGIC MASALA POTATO CHIPS",
      "confidence": 0.98,
      "source": "ocr",
      "bounding_box": { "x": 120, "y": 144, "width": 560, "height": 72 }
    },
    "manufacturer": {
      "field": "manufacturer",
      "value": "Desi Snacks Ltd., Plot 14, Phase II, Industrial Area, Okhla, New Delhi - 110020",
      "confidence": 0.93,
      "source": "ocr",
      "bounding_box": { "x": 80, "y": 1068, "width": 640, "height": 60 }
    },
    "packer": {
      "field": "packer",
      "value": null,
      "confidence": 0.0,
      "source": "ocr",
      "bounding_box": null
    },
    "importer": {
      "field": "importer",
      "value": null,
      "confidence": 0.0,
      "source": "ocr",
      "bounding_box": null
    },
    "net_quantity": {
      "field": "net_quantity",
      "value": "120 gms",
      "confidence": 0.96,
      "source": "ocr",
      "bounding_box": { "x": 112, "y": 780, "width": 272, "height": 60 }
    },
    "mrp": {
      "field": "mrp",
      "value": "₹40",
      "confidence": 0.97,
      "source": "ocr",
      "bounding_box": { "x": 112, "y": 864, "width": 248, "height": 60 }
    },
    "packing_date": {
      "field": "packing_date",
      "value": "06/2026",
      "confidence": 0.95,
      "source": "ocr",
      "bounding_box": { "x": 112, "y": 1008, "width": 328, "height": 48 }
    },
    "manufacturing_date": {
      "field": "manufacturing_date",
      "value": null,
      "confidence": 0.0,
      "source": "ocr",
      "bounding_box": null
    },
    "consumer_care": {
      "field": "consumer_care",
      "value": "1800-200-4545 Email: care@desisnacks.com",
      "confidence": 0.92,
      "source": "ocr",
      "bounding_box": { "x": 80, "y": 1140, "width": 640, "height": 48 }
    },
    "country_of_origin": {
      "field": "country_of_origin",
      "value": "India",
      "confidence": 0.99,
      "source": "ocr",
      "bounding_box": { "x": 440, "y": 780, "width": 264, "height": 60 }
    },
    "batch_or_lot_number": {
      "field": "batch_or_lot_number",
      "value": "LOT-2026-B88",
      "confidence": 0.95,
      "source": "ocr",
      "bounding_box": { "x": 112, "y": 1008, "width": 328, "height": 48 }
    }
  },
  "extracted_fields_count": 8,
  "missing_fields_count": 3,
  "provider": "MockExtractionProvider",
  "processing_time_ms": 22.64
}
```

### 8. Retrieve Cached Declaration Extraction Results
- **Route**: `GET /api/v1/inspections/{inspection_id}/extract`
- **Description**: Returns previously computed extraction for an inspection.
- **Response**: `200 OK` (or `404 Not Found` if extraction has not been triggered yet)

### 9. List Legal Metrology Rules
- **Route**: `GET /api/v1/rules`
- **Query Parameters**:
  - `version`: Optional rule version (defaults to latest `2026.1`)
  - `category`: Optional product category applicability filter (`food`, `packaged_commodity`, `all`)
  - `field`: Optional target declaration field (`mrp`, `net_quantity`, etc.)
  - `enabled_only`: Boolean (`true`/`false`)
- **Response**: `200 OK`
```json
{
  "rules": [
    {
      "rule_id": "LM-MRP-001",
      "name": "MRP Mandatory Declaration",
      "description": "Retail sale price of the package shall be declared on every package as Maximum Retail Price (MRP).",
      "requirement": "The package must visibly declare the retail sale price as 'Maximum Retail Price' or 'MRP' inclusive of all taxes.",
      "applicable_product_categories": ["all", "packaged_commodity"],
      "field_to_validate": "mrp",
      "validation_type": "REQUIRED",
      "severity": "CRITICAL",
      "effective_from": "2011-11-01",
      "effective_until": null,
      "rule_version": "2026.1",
      "source_reference": "Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(e)",
      "enabled": true
    }
  ],
  "total": 10,
  "selected_version": "2026.1",
  "available_versions": ["2026.1", "2024.1"]
}
```

### 10. Get Single Rule by ID
- **Route**: `GET /api/v1/rules/{rule_id}`
- **Query Parameters**:
  - `version`: Optional rule version
- **Response**: `200 OK`
```json
{
  "rule_id": "LM-MRP-001",
  "name": "MRP Mandatory Declaration",
  "field_to_validate": "mrp",
  "validation_type": "REQUIRED",
  "severity": "CRITICAL",
  "rule_version": "2026.1",
  "source_reference": "Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(e)",
  "enabled": true
}
```

### 11. Evaluate Legal Metrology Compliance
- **Route**: `POST /api/v1/inspections/{inspection_id}/evaluate`
- **Query Parameters**:
  - `category`: Product category (defaults to `packaged_commodity`)
  - `rule_version`: Statutory rule catalog version (defaults to latest `2026.1`)
- **Description**: Deterministically screens extracted packaging declarations against versioned statutory rules. Never converts low-confidence AI extraction into a definitive violation; uncertain cases map to `MANUAL_REVIEW`.
- **Response**: `200 OK`
```json
{
  "inspection_id": "insp_9957738ee43d",
  "overall_status": "POTENTIAL_VIOLATION",
  "risk_score": 30,
  "violations": [
    {
      "rule_id": "LM-MRP-002",
      "requirement": "The MRP declaration must include the wording 'incl. of all taxes' or 'inclusive of all taxes'.",
      "field": "mrp",
      "extracted_value": "₹40",
      "detection_status": "FOUND",
      "status": "POTENTIAL_VIOLATION",
      "reason": "MRP declaration ('₹40') does not visibly specify 'inclusive of all taxes'.",
      "severity": "HIGH",
      "confidence": 0.97,
      "evidence_reference": {
        "bounding_box": { "x": 112, "y": 864, "width": 248, "height": 60 },
        "source": "ocr"
      }
    }
  ],
  "checks": [ ... ],
  "product_category": "packaged_commodity",
  "rule_version": "2026.1",
  "timestamp": "2026-09-03T15:35:48.123456+00:00"
}
```

### 12. Get Cached Compliance Evaluation
- **Route**: `GET /api/v1/inspections/{inspection_id}/compliance`
- **Response**: `200 OK`

### 13. Retrieve Grounded Evidence Ledger
- **Route**: `GET /api/v1/inspections/{inspection_id}/evidence`
- **Query Parameters**:
  - `rule_id`: Optional statutory rule filter (e.g. `LM-MRP-001`)
  - `type`: Optional evidence type filter (`ABSENCE`, `INCORRECT_DECLARATION`, `UNCERTAIN`, `DETECTED_DECLARATION`)
- **Description**: Returns the grounded evidence ledger linking statutory rules to extracted declarations and physical image bounding boxes. Never fabricates bounding boxes for missing declarations.
- **Response**: `200 OK`
```json
{
  "inspection_id": "insp_28b43e9636d7",
  "total": 9,
  "evidence": [
    {
      "evidence_id": "ev_4f2d1e90ab",
      "inspection_id": "insp_28b43e9636d7",
      "rule_id": "LM-MFD-001",
      "type": "DETECTED_DECLARATION",
      "image_id": "evidence_product.jpg",
      "bounding_box": {
        "x": 80,
        "y": 1068,
        "width": 640,
        "height": 60
      },
      "detected_text": "Desi Snacks Ltd., Plot 14, Phase II, Industrial Area, Okhla, New Delhi - 110020",
      "confidence": 0.94,
      "explanation": "Evidence of compliance: Grounded declaration satisfies rule requirement.",
      "evidence_available": true
    },
    {
      "evidence_id": "ev_8b91a27f0c",
      "inspection_id": "insp_28b43e9636d7",
      "rule_id": "LM-MRP-001",
      "type": "ABSENCE",
      "image_id": "evidence_product.jpg",
      "bounding_box": null,
      "detected_text": null,
      "confidence": 0.0,
      "explanation": "Evidence of absence: The mandatory declaration 'mrp' was verified absent after scanning the package label.",
      "evidence_available": false
    }
  ],
  "summary": {
    "detected_count": 7,
    "incorrect_count": 2,
    "absence_count": 1,
    "uncertain_count": 0
  }
}
```

### 14. Generate PDF Inspection Report
- **Route**: `POST /api/v1/inspections/{inspection_id}/report`
- **Also Available**: `GET /api/v1/inspections/{inspection_id}/report`
- **Description**: Generates an official, publication-quality Legal Metrology PDF inspection report. Contains embedded packaging photograph with spatial evidence overlays, inspector information, and an audit table strictly differentiating DETECTED FACT, RULE REQUIREMENT, and SYSTEM FINDING. Includes the statutory disclaimer that AI findings are non-binding preliminary screening signals.
- **Response**: `200 OK` (`application/pdf`)

### 15. Batch Package Inspection
- **Route**: `POST /api/v1/inspections/batch`
- **Description**: Ingests multiple package photographs simultaneously (e.g. up to 20 images). Runs the full screening pipeline (Image Ingestion -> OCR -> Declaration Extraction -> Deterministic Rule Evaluation -> Persistence) for each package independently.
- **Resilience**: A single image failure (such as unsupported mime-type or file corruption) does not fail the batch; each item maintains its own isolated status and error state.
- **Query Parameters**:
  - `category` (optional, default: `"packaged_commodity"`): Product commodity category
  - `rule_version` (optional, default: `"2026.1"`): Statutory ruleset version
- **Response**: `200 OK` (`BatchInspectionResponse`)
  - `total`: Total packages
  - `compliant_count`: Compliant packages count
  - `potential_violations_count`: Potential violations count
  - `manual_review_count`: Manual review count
  - `high_risk_count`: High-risk packages count (risk score >= 30)
  - `failed_count`: Failed images count
  - `results`: List of `BatchInspectionItemResult` containing product name, status, risk score, violations count, average confidence, and error detail if failed.

### 16. Manufacturer-Level Compliance Analytics
- **Route**: `GET /api/v1/analytics/manufacturers`
- **Description**: Aggregates historical package commodity inspections across manufacturers with repeated issues breakdown. Adheres strictly to non-defamatory, statutorily neutral language (e.g. *"Repeated potential issues detected."* or *"No screening issues flagged."*).
- **Query Parameters**:
  - `start_date` (optional, ISO format): Minimum inspection timestamp
  - `end_date` (optional, ISO format): Maximum inspection timestamp
  - `manufacturer` (optional, string): Case-insensitive manufacturer substring search
  - `product_category` (optional, string): Filter by product category (e.g. `food`, `packaged_commodity`)
  - `violation_type` (optional, string): Filter by statutory breach type (e.g. `MISSING_DECLARATION`)
- **Response**: `200 OK` (`ManufacturerAnalyticsResponse`)
  - `total_manufacturers`: Count of distinct manufacturers analyzed
  - `total_inspections`: Total package samples aggregated
  - `total_potential_violations`: Cumulative potential violations
  - `total_repeated_issues`: Total recurring pattern defects
  - `manufacturers`: List of `ManufacturerAnalyticsItem` containing name, counts, compliance rate, average risk, neutral status label, and repeated issues breakdown (`field`, `label`, `count`).

### 17. Submit Human Inspector Review
- **Route**: `POST /api/v1/inspections/{inspection_id}/review`
- **Description**: Records official inspector determination (`CONFIRM_FINDING`, `REJECT_FINDING`, `REQUEST_MANUAL_VERIFICATION`, `MARK_NOT_APPLICABLE`) along with optional statutory rationale or commentary.
- **Traceability Guarantee**: The original AI screening result (`overall_status`, `risk_score`) is **never** overwritten; both the original AI perception and the human decision are preserved side-by-side in PostgreSQL and logged in `AuditLog`.
- **Payload**:
  - `decision` (string, required): `CONFIRM_FINDING` | `REJECT_FINDING` | `REQUEST_MANUAL_VERIFICATION` | `MARK_NOT_APPLICABLE`
  - `comment` (string, optional): Inspector rationale or physical inspection notes
  - `reviewer` (string, optional): Inspector identifier (default: `"inspector_lm"`)
- **Response**: `200 OK` (`ReviewRecordResponse`)

### 18. Get Inspection Human Review History
- **Route**: `GET /api/v1/inspections/{inspection_id}/reviews`
- **Description**: Returns the chronological audit trail of human inspector review determinations for an inspection.
- **Response**: `200 OK` (`List[ReviewRecordResponse]`)

### 19. Retrieve Current User Identity & Entra ID Role
- **Route**: `GET /api/v1/admin/roles/current`
- **Description**: Returns authenticated user identity and resolved role permissions under Microsoft Entra ID integration.
- **Response**: `200 OK`

### 20. Retrieve Regulatory System Audit Logs
- **Route**: `GET /api/v1/admin/audit-logs`
- **Authorization**: `SUPERVISOR` or `ADMIN` role required (`403 Forbidden` if accessed by Inspector).
- **Description**: Returns chronological regulatory ledger of all system actions (uploads, evaluations, human reviews, provisioning).
- **Response**: `200 OK` (`List[AuditLogItemResponse]`)

### 21. Provision Platform Officer
- **Route**: `POST /api/v1/admin/users`
- **Authorization**: `ADMIN` role required.
- **Description**: Provisions an officer account with specified role (`INSPECTOR`, `SUPERVISOR`, `ADMIN`).
- **Response**: `201 Created` (`UserRecordResponse`)

### 22. List Platform Users
- **Route**: `GET /api/v1/admin/users`
- **Authorization**: `ADMIN` role required.
- **Description**: Lists all registered enforcement officers and administrators.
- **Response**: `200 OK` (`List[UserRecordResponse]`)
