export interface SubCheckItemDTO {
  rule_id: string;
  rule_title: string;
  section: string;
  status: 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW' | 'NOT_APPLICABLE' | 'POTENTIAL_VIOLATION' | 'MANUAL_REVIEW';
  reason: string;
  confidence: number;
  extracted_value?: string | null;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface CanonicalRequirementDTO {
  canonical_id: string;
  title: string;
  statutory_rule: string;
  field: string;
  status: 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW' | 'NOT_APPLICABLE' | 'POTENTIAL_VIOLATION' | 'MANUAL_REVIEW';
  extracted_value?: string | null;
  confidence: number;
  overall_reason: string;
  sub_checks: SubCheckItemDTO[];
  human_review?: {
    canonical_id: string;
    decision: string;
    reason: string;
    remarks?: string;
    reviewer: string;
    timestamp: string;
    original_ai_status: string;
  } | null;
}

export interface RuleCheckResult {
  rule_id: string;
  requirement: string;
  field: string;
  extracted_value: string | null;
  detection_status: 'FOUND' | 'NOT_FOUND' | 'UNCLEAR' | 'NOT_APPLICABLE';
  status: 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW' | 'POTENTIAL_VIOLATION' | 'MANUAL_REVIEW' | 'NOT_APPLICABLE';
  reason: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: number;
  evidence_reference?: {
    bounding_box?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
    source?: string;
    evidence_text?: string;
  } | null;
}

export interface ComplianceEvaluationResult {
  inspection_id: string;
  overall_status: 'COMPLIANT' | 'CONFIRMED_VIOLATION' | 'NON_COMPLIANT' | 'NEEDS_REVIEW' | 'POTENTIAL_VIOLATION' | 'MANUAL_REVIEW' | 'REVIEW_PENDING';
  risk_score: number;
  screening_priority_score?: number;
  confirmed_violations_count?: number;
  items_needing_review_count?: number;
  evidence_coverage_percent?: number;
  canonical_requirements?: CanonicalRequirementDTO[];
  violations: RuleCheckResult[];
  checks: RuleCheckResult[];
  human_reviews?: Record<string, any>;
  product_category: string;
  rule_version: string;
  timestamp: string;
}
