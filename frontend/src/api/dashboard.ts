import { DashboardMetrics } from '../types/dashboard';
import { fetchJson } from './client';

export const dashboardApi = {
  getMetrics: async (): Promise<DashboardMetrics> => {
    return fetchJson<DashboardMetrics>('/inspections/meta/dashboard', {
      method: 'GET',
    });
  },

  listAllInspections: async (): Promise<any[]> => {
    return fetchJson<any[]>('/inspections', {
      method: 'GET',
    });
  },

  getInspectionDetail: async (inspectionId: string): Promise<any> => {
    return fetchJson<any>(`/inspections/${inspectionId}`, {
      method: 'GET',
    });
  },
};
