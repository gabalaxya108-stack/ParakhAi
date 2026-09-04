import { fetchJson } from './client';
import {
  RuleModel,
  RuleListResponse,
  RegulatoryDocumentDTO,
  RegulatoryRuleDTO,
  RuleAmendmentDTO,
  RegulatoryCatalogSummary
} from '../types/rules';

export const rulesApi = {
  getRules: async (params?: {
    version?: string;
    category?: string;
    field?: string;
    status?: string;
  }): Promise<RuleListResponse> => {
    try {
      const q = new URLSearchParams();
      if (params?.version) q.append('version', params.version);
      if (params?.category) q.append('category', params.category);
      if (params?.field) q.append('field', params.field);
      if (params?.status) q.append('status', params.status);

      const qs = q.toString() ? `?${q.toString()}` : '';
      const regRules = await fetchJson<RegulatoryRuleDTO[]>(`/regulatory/rules${qs}`);
      const mappedRules: RuleModel[] = (regRules || []).map((r: RegulatoryRuleDTO) => ({
        rule_id: r.rule_id,
        name: r.title,
        title: r.title,
        description: r.title,
        requirement: r.requirement,
        applicable_product_categories: r.applicable_categories,
        applicable_categories: r.applicable_categories,
        field_to_validate: r.field_to_validate,
        validation_type: r.validation_type,
        severity: r.severity,
        effective_from: r.effective_from,
        effective_until: r.effective_until ?? null,
        rule_version: r.rule_version,
        section: r.section,
        sub_rule: r.sub_rule,
        source_reference: r.source_page || r.section,
        source_url: r.source_url,
        source_page: r.source_page,
        status: r.status,
        enabled: r.status === 'ACTIVE'
      }));

      return {
        rules: mappedRules,
        total: mappedRules.length,
        selected_version: params?.version || '2026.1',
        available_versions: ['2026.1', '2011']
      };
    } catch {
      const q = new URLSearchParams();
      if (params?.version) q.append('version', params.version);
      if (params?.category) q.append('category', params.category);
      const qs = q.toString() ? `?${q.toString()}` : '';
      return fetchJson<RuleListResponse>(`/rules${qs}`);
    }
  },

  getRuleById: async (ruleId: string, version?: string): Promise<RuleModel> => {
    const qs = version ? `?version=${version}` : '';
    return fetchJson<RuleModel>(`/regulatory/rules/${ruleId}${qs}`);
  },

  getRuleVersions: async (): Promise<{ available_versions: string[]; latest_version: string }> => {
    const summary = await fetchJson<RegulatoryCatalogSummary>('/regulatory/summary');
    return {
      available_versions: summary.available_versions,
      latest_version: summary.latest_version
    };
  },

  getRegulatorySummary: async (): Promise<RegulatoryCatalogSummary> => {
    return fetchJson<RegulatoryCatalogSummary>('/regulatory/summary');
  },

  getRegulatoryDocuments: async (): Promise<RegulatoryDocumentDTO[]> => {
    return fetchJson<RegulatoryDocumentDTO[]>('/regulatory/documents');
  },

  getRuleAmendments: async (ruleId?: string): Promise<RuleAmendmentDTO[]> => {
    const qs = ruleId ? `?rule_id=${ruleId}` : '';
    return fetchJson<RuleAmendmentDTO[]>(`/regulatory/amendments${qs}`);
  },

  transitionRuleStatus: async (ruleId: string, action: 'APPROVE' | 'ACTIVATE' | 'SUPERSEDE' | 'REJECT', effectiveUntil?: string): Promise<any> => {
    return fetchJson(`/regulatory/rules/${ruleId}/transition`, {
      method: 'POST',
      body: JSON.stringify({ action, effective_until: effectiveUntil })
    });
  }
};
