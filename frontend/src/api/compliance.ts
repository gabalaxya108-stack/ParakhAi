import { ComplianceEvaluationResult } from '../types/compliance';
import { fetchJson } from './client';

export const complianceApi = {
  evaluateCompliance: async (
    inspectionId: string,
    category: string = 'packaged_commodity',
    ruleVersion?: string
  ): Promise<ComplianceEvaluationResult> => {
    const query = new URLSearchParams();
    query.append('category', category);
    if (ruleVersion) query.append('rule_version', ruleVersion);

    return fetchJson<ComplianceEvaluationResult>(
      `/inspections/${inspectionId}/evaluate?${query.toString()}`,
      { method: 'POST' }
    );
  },

  getCachedCompliance: async (inspectionId: string): Promise<ComplianceEvaluationResult> => {
    return fetchJson<ComplianceEvaluationResult>(`/inspections/${inspectionId}/compliance`, {
      method: 'GET',
    });
  },
};
