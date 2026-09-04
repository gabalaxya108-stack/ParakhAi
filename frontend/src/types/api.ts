export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
  timestamp: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}
