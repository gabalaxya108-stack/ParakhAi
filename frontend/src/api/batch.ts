import { API_BASE_URL } from './client';
import { BatchInspectionResponse } from '../types/batch';

export const batchApi = {
  uploadBatch: async (
    files: File[],
    category: string = 'packaged_commodity',
    ruleVersion: string = '2026.1',
    onProgress?: (progressPercent: number) => void
  ): Promise<BatchInspectionResponse> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const query = new URLSearchParams({ category, rule_version: ruleVersion });

    return new Promise<BatchInspectionResponse>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE_URL}/inspections/batch?${query.toString()}`);

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
            const data = JSON.parse(xhr.responseText);
            resolve(data);
          } catch (e) {
            reject(new Error('Invalid response from server'));
          }
        } else {
          try {
            const errData = JSON.parse(xhr.responseText);
            reject(new Error(errData.detail || `Batch request failed (${xhr.status})`));
          } catch {
            reject(new Error(`Batch request failed (${xhr.status})`));
          }
        }
      };

      xhr.onerror = () => reject(new Error('Network error during batch upload'));
      xhr.send(formData);
    });
  },
};
