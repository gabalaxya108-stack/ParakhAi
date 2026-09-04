export interface RepeatedIssue {
  field: string;
  label: string;
  count: number;
  rule_id?: string | null;
  violation_type?: string | null;
}

export interface ManufacturerAnalyticsItem {
  manufacturer_name: string;
  total_inspections: number;
  compliant_inspections: number;
  potential_violations: number;
  manual_reviews: number;
  violation_categories: Record<string, number>;
  repeated_issues: RepeatedIssue[];
  compliance_rate: number;
  average_risk: number;
  status_label: string;
  latest_inspection_date?: string | null;
}

export interface ManufacturerAnalyticsResponse {
  total_manufacturers: number;
  total_inspections: number;
  total_potential_violations: number;
  total_repeated_issues: number;
  manufacturers: ManufacturerAnalyticsItem[];
}
