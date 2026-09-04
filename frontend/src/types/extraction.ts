import { PixelBoundingBox } from './ocr';

export interface CandidateObservation {
  value: string | null;
  source: string;
  confidence: number;
  evidence_text?: string | null;
  bounding_box?: PixelBoundingBox | null;
}

export interface ReconciliationDetail {
  field: string;
  candidates: CandidateObservation[];
  resolution: string;
  conflict_detected: boolean;
  reconciliation_notes?: string | null;
}

export interface FieldExtractionResult {
  field: string;
  value: string | null;
  confidence: number;
  source: string;
  bounding_box: PixelBoundingBox | null;
  evidence_text?: string | null;
  conflict_detected?: boolean;
  candidates?: CandidateObservation[];
}

export interface ExtractedFieldsContainer {
  product_name: FieldExtractionResult;
  manufacturer: FieldExtractionResult;
  packer: FieldExtractionResult;
  importer: FieldExtractionResult;
  net_quantity: FieldExtractionResult;
  mrp: FieldExtractionResult;
  packing_date: FieldExtractionResult;
  manufacturing_date: FieldExtractionResult;
  consumer_care: FieldExtractionResult;
  country_of_origin: FieldExtractionResult;
  batch_or_lot_number: FieldExtractionResult;
}

export interface ExtractionResponse {
  inspection_id: string;
  fields: ExtractedFieldsContainer;
  extracted_fields_count: number;
  missing_fields_count: number;
  provider: string;
  processing_time_ms: number;
  vision_provider?: string | null;
  vision_status?: string | null;
  preprocessing_status?: string | null;
  reconciliation?: Record<string, ReconciliationDetail> | null;
}

export interface InspectionDebugDossier {
  inspection_id: string;
  original_image_url: string;
  processed_image_url?: string | null;
  preprocessing_status: string;
  preprocessing_metadata: Record<string, any>;
  tesseract: {
    text: string;
    total_blocks: number;
    average_confidence: number;
    processing_time_ms: number;
    blocks: any[];
  };
  vision: {
    model: string;
    status: string;
    raw_declarations: Record<string, any>;
    processing_time_ms: number;
  };
  reconciliation: Record<string, ReconciliationDetail>;
  rule_engine_input: Record<string, any>;
  rule_engine_output: Record<string, any>;
}
