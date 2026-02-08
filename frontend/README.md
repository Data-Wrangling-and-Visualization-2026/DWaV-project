# WVS Values Explorer Frontend

A web interface for visualizing World Values Survey data with interactive 3D visualization.

## Features

- **3D Visualization**: Interactive 3D scatter plot using React-Three-Fiber
- **Filtering**: Filter data by year, region, and country
- **Details Panel**: View detailed information about selected data points
- **Timeseries Charts**: Visualize country evolution over time

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Backend API

The frontend expects the backend API to be running at `http://localhost:8000` with the following endpoints:

- `GET /health` - Health check
- `GET /data` - Get data points (supports `?year=`, `?country=`, `?region=` query params)
- `GET /timeseries?country=...` - Get timeseries data for a country

## Project Structure

```
src/
  components/
    Scene3D.tsx          # 3D visualization component
    Filters.tsx          # Filter controls
    DetailsPanel.tsx     # Details panel for selected point
    TimeseriesChart.tsx  # Chart component for timeseries
  services/
    api.ts              # API service layer
  types.ts              # TypeScript type definitions
  store.ts              # Zustand state management
  App.tsx               # Main app component
  main.tsx              # Entry point
```

## Technologies

- React 18
- TypeScript
- Vite
- React-Three-Fiber (3D visualization)
- Zustand (state management)
- Recharts (timeseries charts)
- Tailwind CSS (styling)
