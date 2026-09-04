import { OCRResult } from '../types/ocr';
import { fetchJson } from './client';

export const ocrApi = {
  extractOcr: async (inspectionId: string): Promise<OCRResult> => {
    return fetchJson<OCRResult>(`/inspections/${inspectionId}/ocr`, {
      method: 'POST',
    });
  },

  getCachedOcr: async (inspectionId: string): Promise<OCRResult> => {
    return fetchJson<OCRResult>(`/inspections/${inspectionId}/ocr`, {
      method: 'GET',
    });
  },
};
