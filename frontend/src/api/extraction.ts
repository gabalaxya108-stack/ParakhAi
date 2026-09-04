import { ExtractionResponse } from '../types/extraction';
import { fetchJson } from './client';

export const extractionApi = {
  extractDeclarations: async (inspectionId: string): Promise<ExtractionResponse> => {
    return fetchJson<ExtractionResponse>(`/inspections/${inspectionId}/extract`, {
      method: 'POST',
    });
  },

  getCachedExtraction: async (inspectionId: string): Promise<ExtractionResponse> => {
    return fetchJson<ExtractionResponse>(`/inspections/${inspectionId}/extract`, {
      method: 'GET',
    });
  },
};
