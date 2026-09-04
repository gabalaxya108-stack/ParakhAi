import { API_BASE_URL } from './client';
export const reportApi = {
  downloadReport: async (inspectionId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/inspections/${inspectionId}/report`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to generate report (status ${response.status})`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Inspection_Report_${inspectionId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};
