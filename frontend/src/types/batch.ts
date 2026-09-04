export interface BatchInspectionItem {
  inspection_id: string | null;
  filename: string;
  product_name: string;
  status: 'COMPLIANT' | 'POTENTIAL_VIOLATION' | 'MANUAL_REVIEW' | 'FAILED';
  risk_score: number;
  violations_count: number;
  average_confidence: number;
  created_at: string;
  success: boolean;
  error?: string | null;
}

export interface BatchInspectionResponse {
  batch_id: string;
  total: number;
  compliant_count: number;
  potential_violations_count: number;
  manual_review_count: number;
  high_risk_count: number;
  failed_count: number;
  results: BatchInspectionItem[];
}
