export interface PixelBoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface NormalizedBoundingBox {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
}

export interface OCRBlock {
  text: string;
  confidence: number;
  bounding_box: PixelBoundingBox;
  normalized_box?: NormalizedBoundingBox;
  page_number: number;
}

export interface OCRResult {
  inspection_id: string;
  full_text: string;
  blocks: OCRBlock[];
  total_blocks: number;
  image_width: number;
  image_height: number;
  provider: string;
  version?: string;
  languages?: string[];
  processing_time_ms: number;
  results?: Array<{
    text: string;
    confidence: number;
    bounding_box: PixelBoundingBox;
  }>;
}
