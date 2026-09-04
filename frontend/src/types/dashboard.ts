export interface DashboardMetrics {
  total_inspections: number;
  compliant_count: number;
  potential_violations_count: number;
  manual_review_count: number;
  pending_evaluation_count: number;
  average_risk_score: number;
  recent_inspections: Array<{
    inspection_id: string;
    filename: string;
    mime_type: string;
    file_size: number;
    created_at: string;
    image_url: string;
    status: string;
    compliance_summary?: {
      overall_status: 'COMPLIANT' | 'POTENTIAL_VIOLATION' | 'MANUAL_REVIEW' | 'NOT_EVALUATED';
      risk_score: number;
      violations_count: number;
      product_category: string;
      product_name?: string | null;
    };
  }>;
}
