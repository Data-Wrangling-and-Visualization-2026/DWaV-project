import { create } from 'zustand';
import type { DataPoint, DataFilters, TimeseriesPoint } from './types';

interface AppState {
  data: DataPoint[];
  selectedPoint: DataPoint | null;
  timeseries: TimeseriesPoint[];
  filters: DataFilters;
  isLoading: boolean;
  error: string | null;
  
  setData: (data: DataPoint[]) => void;
  setSelectedPoint: (point: DataPoint | null) => void;
  setTimeseries: (timeseries: TimeseriesPoint[]) => void;
  setFilters: (filters: Partial<DataFilters>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  data: [],
  selectedPoint: null,
  timeseries: [],
  filters: {},
  isLoading: false,
  error: null,

  setData: (data) => set({ data }),
  setSelectedPoint: (point) => set({ selectedPoint: point }),
  setTimeseries: (timeseries) => set({ timeseries }),
  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
