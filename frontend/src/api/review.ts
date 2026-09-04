import { API_BASE_URL } from './client';
export interface ReviewSubmissionPayload {
  decision: 'CONFIRM_FINDING' | 'REJECT_FINDING' | 'REQUEST_MANUAL_VERIFICATION' | 'MARK_NOT_APPLICABLE';
  comment?: string;
  reviewer?: string;
}

export interface ReviewRecord {
  review_id: number;
  inspection_id: string;
  reviewer: string;
  decision: string;
  decision_label: string;
  comment?: string | null;
  timestamp: string;
  original_ai_status: string;
  original_ai_risk_score: number;
}

export const reviewApi = {
  submitReview: async (inspectionId: string, payload: ReviewSubmissionPayload): Promise<ReviewRecord> => {
    const res = await fetch(`${API_BASE_URL}/inspections/${inspectionId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to submit review (${res.status})`);
    }
    return res.json();
  },

  getReviews: async (inspectionId: string): Promise<ReviewRecord[]> => {
    const res = await fetch(`${API_BASE_URL}/inspections/${inspectionId}/reviews`);
    if (!res.ok) {
      return [];
    }
    return res.json();
  },
};
