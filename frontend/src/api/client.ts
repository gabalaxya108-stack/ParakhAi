import { ApiError } from '../types/api';

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000/api/v1'
).replace(/\/+$/, '');

export const BACKEND_SERVER_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '') || 'http://localhost:8000';

const BASE_URL = API_BASE_URL;

export class ApiClientError extends Error {
  public code: string;
  public details?: unknown;
  public timestamp: string;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiClientError';
    this.code = error.code;
    this.details = error.details;
    this.timestamp = error.timestamp;
  }
}

export async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${BASE_URL}${cleanEndpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options?.headers || {}),
  };

  try {
    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      let errorData: { error?: ApiError; detail?: string } = {};
      try {
        errorData = await response.json();
      } catch {
        // Response was not JSON
      }

      const error: ApiError = errorData.error || {
        code: `HTTP_${response.status}`,
        message: errorData.detail || response.statusText || 'An unexpected error occurred',
        timestamp: new Date().toISOString(),
      };

      throw new ApiClientError(error);
    }

    return (await response.json()) as T;
  } catch (err) {
    if (err instanceof ApiClientError) {
      throw err;
    }
    throw new ApiClientError({
      code: 'NETWORK_ERROR',
      message: err instanceof Error ? err.message : 'Network request failed',
      timestamp: new Date().toISOString(),
    });
  }
}
