import { fetchJson } from './client';
import { HealthResponse } from '../types/health';

export const healthApi = {
  getHealth: async (): Promise<HealthResponse> => {
    return fetchJson<HealthResponse>('/health');
  },
};
