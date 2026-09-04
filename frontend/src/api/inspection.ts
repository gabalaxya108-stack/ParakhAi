import { InspectionUploadResponse } from '../types/inspection';
import { DashboardMetrics } from '../types/dashboard';
import { OCRResult } from '../types/ocr';
import { ExtractionResponse, InspectionDebugDossier } from '../types/extraction';
import { ApiClientError } from './client';

import { API_BASE_URL } from './client';
const BASE_URL = API_BASE_URL;

export const inspectionApi = {
  uploadImage: async (
    file: File,
    onProgress?: (progressPercent: number) => void
  ): Promise<InspectionUploadResponse> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append('file', file);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${BASE_URL}/inspections`);

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText) as InspectionUploadResponse;
            resolve(response);
          } catch (e) {
            reject(
              new ApiClientError({
                code: 'INVALID_JSON',
                message: 'Failed to parse server response',
                timestamp: new Date().toISOString(),
              })
            );
          }
        } else {
          let errorData: any = {};
          try {
            errorData = JSON.parse(xhr.responseText);
          } catch {
            // Non-JSON response
          }

          const error = errorData.error || {
            code: `HTTP_${xhr.status}`,
            message: errorData.detail || xhr.statusText || 'Upload failed',
            timestamp: new Date().toISOString(),
          };

          reject(new ApiClientError(error));
        }
      };

      xhr.onerror = () => {
        reject(
          new ApiClientError({
            code: 'NETWORK_ERROR',
            message: 'Network connection failed while uploading image',
            timestamp: new Date().toISOString(),
          })
        );
      };

      xhr.send(formData);
    });
  },

  getInspection: async (inspectionId: string): Promise<any> => {
    const response = await fetch(`${BASE_URL}/inspections/${inspectionId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch inspection ${inspectionId}`);
    }
    return response.json();
  },

  listInspections: async (): Promise<any[]> => {
    const response = await fetch(`${BASE_URL}/inspections`);
    if (!response.ok) {
      throw new Error('Failed to list inspections');
    }
    return response.json();
  },

  getDashboardMetrics: async (): Promise<DashboardMetrics> => {
    const response = await fetch(`${BASE_URL}/inspections/meta/dashboard`);
    if (!response.ok) {
      throw new Error('Failed to fetch dashboard metrics');
    }
    return response.json();
  },

  getOcrResult: async (inspectionId: string): Promise<OCRResult> => {
    const response = await fetch(`${BASE_URL}/inspections/${inspectionId}/ocr`);
    if (!response.ok) {
      throw new Error(`Failed to fetch OCR result for ${inspectionId}`);
    }
    return response.json();
  },

  extractOcr: async (inspectionId: string): Promise<OCRResult> => {
    const response = await fetch(`${BASE_URL}/inspections/${inspectionId}/ocr`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to extract OCR for ${inspectionId}`);
    }
    return response.json();
  },

  extractDeclarations: async (inspectionId: string): Promise<ExtractionResponse> => {
    const response = await fetch(`${BASE_URL}/inspections/${inspectionId}/extract`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to extract declarations for ${inspectionId}`);
    }
    return response.json();
  },

  compareListing: async (inspectionId: string, listingData: any): Promise<any> => {
    const response = await fetch(`${BASE_URL}/inspections/${inspectionId}/compare-listing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(listingData),
    });
    if (!response.ok) {
      throw new Error(`Failed to compare e-commerce listing for ${inspectionId}`);
    }
    return response.json();
  },

  getExtractionResult: async (inspectionId: string): Promise<ExtractionResponse> => {
    const response = await fetch(`${BASE_URL}/inspections/${inspectionId}/extract`);
    if (!response.ok) {
      throw new Error(`Failed to fetch extraction result for ${inspectionId}`);
    }
    return response.json();
  },

  getDebugDossier: async (inspectionId: string): Promise<InspectionDebugDossier> => {
    const response = await fetch(`${BASE_URL}/inspections/${inspectionId}/debug`);
    if (!response.ok) {
      throw new Error(`Failed to fetch debug dossier for ${inspectionId}`);
    }
    return response.json();
  },
};
