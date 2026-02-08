export interface Values {
  happiness: number;
  life_satisfaction: number;
  trust: number;
  religiosity: number;
  political_orientation: number;
  moral_values: number;
}

export interface Embedding {
  x: number;
  y: number;
  z: number;
}

export interface DataPoint {
  country: string;
  region: string;
  year: number;
  values: Values;
  embedding: Embedding;
}

export interface TimeseriesPoint {
  year: number;
  happiness: number;
  trust: number;
  life_satisfaction?: number;
  religiosity?: number;
  political_orientation?: number;
  moral_values?: number;
}

export interface HealthResponse {
  status: string;
}

export interface DataFilters {
  year?: number;
  country?: string;
  region?: string;
}
