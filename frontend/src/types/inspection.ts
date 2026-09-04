export interface InspectionUploadResponse {
  inspection_id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  created_at: string;
  image_location: string;
  image_url: string;
  status: string;
}
