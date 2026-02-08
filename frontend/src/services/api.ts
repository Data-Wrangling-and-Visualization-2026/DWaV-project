import type { DataPoint, TimeseriesPoint, HealthResponse, DataFilters } from '../types';

// Use /api when behind nginx proxy (Docker), else direct backend URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log(`[API] Fetching: ${url}`);
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API] Error ${response.status}:`, errorText);
      throw new Error(`API error ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] Success:`, data);
    return data;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error('[API] Network error - CORS or connection issue:', error);
      throw new Error(
        `Cannot connect to backend at ${API_BASE_URL}. ` +
        `Make sure the backend is running and CORS is enabled. ` +
        `Error: ${error.message}`
      );
    }
    throw error;
  }
}

export const api = {
  async healthCheck(): Promise<HealthResponse> {
    return fetchAPI<HealthResponse>('/health');
  },

  async getData(filters?: DataFilters): Promise<DataPoint[]> {
    const params = new URLSearchParams();
    if (filters?.year) params.append('year', filters.year.toString());
    if (filters?.country) params.append('country', filters.country);
    if (filters?.region) params.append('region', filters.region);

    const queryString = params.toString();
    const endpoint = queryString ? `/data?${queryString}` : '/data';
    return fetchAPI<DataPoint[]>(endpoint);
  },

  async getTimeseries(country: string): Promise<TimeseriesPoint[]> {
    return fetchAPI<TimeseriesPoint[]>(`/timeseries?country=${encodeURIComponent(country)}`);
  },
};
