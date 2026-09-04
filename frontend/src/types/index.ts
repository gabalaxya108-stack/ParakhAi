export type ComplianceStatus = 'PASS' | 'FAIL' | 'WARNING' | 'MANUAL_CHECK_REQUIRED';
export type RuleSeverity = 'CRITICAL' | 'MAJOR' | 'MINOR';

export type DeclarationType =
  | 'NAME_AND_ADDRESS'
  | 'GENERIC_NAME'
  | 'NET_QUANTITY'
  | 'RETAIL_SALE_PRICE'
  | 'UNIT_SALE_PRICE'
  | 'DATE_OF_MANUFACTURE'
  | 'EXPIRY_DATE'
  | 'CONSUMER_CARE'
  | 'COUNTRY_OF_ORIGIN'
  | 'NUTRITIONAL_INFO';

export interface BoundingBox {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
  polygon?: number[][];
  label?: string;
  estimated_font_height_mm?: number;
}

export interface ExtractedDeclarationDTO {
  id: string;
  declaration_type: DeclarationType;
  raw_text: string;
  normalized_value: any;
  parsed_attributes: Record<string, any>;
  confidence: number;
  bounding_box: BoundingBox;
  is_manually_edited: boolean;
  edited_by?: string;
  notes?: string;
}

export interface RuleEvaluationResult {
  rule_id: string;
  legal_reference: string;
  rule_title: string;
  severity: RuleSeverity;
  status: ComplianceStatus;
  violation_reason?: string;
  legal_citation: string;
  recommended_action?: string;
  evidence_text?: string;
  evidence_boxes: BoundingBox[];
  inspector_override: boolean;
  override_verdict?: ComplianceStatus;
  override_reason?: string;
  overridden_by?: string;
}

export interface ComplianceScorecard {
  overall_status: ComplianceStatus;
  total_rules: number;
  passed_count: number;
  failed_count: number;
  warning_count: number;
  manual_check_count: number;
  results: RuleEvaluationResult[];
}

export interface InspectionSummaryDTO {
  id: string;
  inspection_number: string;
  commodity_name: string;
  brand_name?: string;
  commodity_category: string;
  status: string;
  overall_compliance: ComplianceStatus;
  created_at: string;
  image_url: string;
  violations_count: number;
}

export interface InspectionDetailResponse {
  id: string;
  inspection_number: string;
  commodity_name: string;
  commodity_category: string;
  brand_name?: string;
  batch_number?: string;
  image_url: string;
  preprocessed_image_url?: string;
  pdp_area_sq_cm: number;
  status: string;
  overall_compliance: ComplianceStatus;
  inspector_name: string;
  inspector_notes?: string;
  inspector_signature?: string;
  declarations: ExtractedDeclarationDTO[];
  compliance_scorecard: ComplianceScorecard;
  created_at: string;
  reviewed_at?: string;
}

export interface RuleDefinition {
  rule_id: string;
  legal_reference: string;
  title: string;
  description: string;
  severity: RuleSeverity;
  target_declaration: DeclarationType;
  penalty_section?: string;
}

export interface AnalyticsSummary {
  total_inspections: number;
  compliant_count: number;
  violation_count: number;
  pending_review_count: number;
  compliance_rate_pct: number;
  top_violations: Array<{
    rule_id: string;
    label: string;
    count: number;
  }>;
}
