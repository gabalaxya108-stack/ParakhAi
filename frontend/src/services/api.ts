import {
  InspectionDetailResponse,
  InspectionSummaryDTO,
  RuleDefinition,
  AnalyticsSummary,
  ComplianceStatus,
  BoundingBox
} from '../types';

import { API_BASE_URL, BACKEND_SERVER_ORIGIN } from '../api/client';

const API_BASE = API_BASE_URL;

export const api = {
  async getInspections(status?: string, compliance?: string): Promise<InspectionSummaryDTO[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (compliance) params.append('compliance', compliance);
    const res = await fetch(`${API_BASE}/inspections?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch inspections');
    return res.json();
  },

  async getInspection(id: string): Promise<InspectionDetailResponse> {
    const res = await fetch(`${API_BASE}/inspections/${id}`);
    if (!res.ok) throw new Error('Failed to fetch inspection details');
    return res.json();
  },

  async createInspection(formData: FormData): Promise<InspectionDetailResponse> {
    const res = await fetch(`${API_BASE}/inspections`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create inspection' }));
      throw new Error(err.detail || 'Failed to create inspection');
    }
    return res.json();
  },

  async updateDeclaration(
    inspectionId: string,
    declId: string,
    data: {
      raw_text?: string;
      normalized_value?: any;
      bounding_box?: BoundingBox;
      notes?: string;
    }
  ): Promise<InspectionDetailResponse> {
    const res = await fetch(`${API_BASE}/inspections/${inspectionId}/declarations/${declId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to update declaration');
    return res.json();
  },

  async submitReview(
    inspectionId: string,
    review: {
      final_verdict: ComplianceStatus;
      inspector_notes: string;
      inspector_signature: string;
      overrides?: Array<{
        rule_id: string;
        override_verdict: ComplianceStatus;
        override_reason: string;
      }>;
    }
  ): Promise<InspectionDetailResponse> {
    const res = await fetch(`${API_BASE}/inspections/${inspectionId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(review)
    });
    if (!res.ok) throw new Error('Failed to submit review');
    return res.json();
  },

  async getRules(): Promise<RuleDefinition[]> {
    const res = await fetch(`${API_BASE}/rules`);
    if (!res.ok) throw new Error('Failed to fetch rules');
    return res.json();
  },

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const res = await fetch(`${API_BASE}/analytics/summary`);
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
  },

  async getConfigProviders(): Promise<any> {
    const res = await fetch(`${API_BASE}/config/providers`);
    if (!res.ok) throw new Error('Failed to fetch providers');
    return res.json();
  },

  getReportPdfUrl(inspectionId: string): string {
    return `${API_BASE}/inspections/${inspectionId}/report.pdf`;
  },

  getImageUrl(path: string): string {
    if (!path) return "";
    if (path.startsWith("http://") || path.startsWith("https://")) return path;
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    return `${BACKEND_SERVER_ORIGIN}${cleanPath}`;
  }
};
