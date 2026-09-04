export interface RuleModel {
  rule_id: string;
  name?: string;
  title?: string;
  description?: string;
  requirement: string;
  applicable_product_categories?: string[];
  applicable_categories?: string[];
  field_to_validate: string;
  validation_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  effective_from: string;
  effective_until: string | null;
  rule_version: string;
  section?: string;
  sub_rule?: string;
  source_reference?: string;
  source_url?: string;
  source_page?: string;
  status?: string;
  enabled?: boolean;
}

export interface RuleListResponse {
  rules: RuleModel[];
  total: number;
  selected_version: string;
  available_versions: string[];
}

export interface RegulatoryDocumentDTO {
  id: string;
  document_name: string;
  document_type: string;
  notification_number?: string;
  publication_date: string;
  effective_date: string;
  source_url?: string;
  source_reference: string;
  content_hash?: string;
  version: string;
  status: string;
}

export interface RegulatoryRuleDTO {
  id: string;
  rule_id: string;
  rule_version: string;
  title: string;
  section: string;
  sub_rule?: string;
  requirement: string;
  applicable_categories: string[];
  field_to_validate: string;
  validation_type: string;
  validation_expression?: Record<string, any>;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  effective_from: string;
  effective_until?: string | null;
  source_document_id?: string;
  source_url?: string;
  source_page?: string;
  source_excerpt?: string;
  status: 'PENDING_REVIEW' | 'APPROVED' | 'ACTIVE' | 'SUPERSEDED' | 'REJECTED';
}

export interface RuleAmendmentDTO {
  id: string;
  document_id: string;
  rule_id: string;
  change_type: string;
  previous_value?: string | null;
  new_value: string;
  effective_from: string;
  effective_until?: string | null;
  explanation?: string | null;
  created_at?: string;
}

export interface RegulatoryCatalogSummary {
  total_rules: number;
  active_rules: number;
  pending_rules: number;
  superseded_rules: number;
  documents_count: number;
  amendments_count: number;
  available_versions: string[];
  latest_version: string;
}
