import { API_BASE_URL } from './client';
import { ManufacturerAnalyticsResponse } from '../types/analytics';

export interface AnalyticsFilterParams {
  startDate?: string;
  endDate?: string;
  manufacturer?: string;
  productCategory?: string;
  violationType?: string;
}

export const analyticsApi = {
  getManufacturerAnalytics: async (filters: AnalyticsFilterParams = {}): Promise<ManufacturerAnalyticsResponse> => {
    const params = new URLSearchParams();
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.manufacturer) params.append('manufacturer', filters.manufacturer);
    if (filters.productCategory && filters.productCategory !== 'ALL') params.append('product_category', filters.productCategory);
    if (filters.violationType && filters.violationType !== 'ALL') params.append('violation_type', filters.violationType);

    const res = await fetch(`${API_BASE_URL}/analytics/manufacturers?${params.toString()}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch manufacturer analytics (${res.status})`);
    }
    return res.json();
  },
};
