import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { TimeseriesPoint } from '../types';

interface TimeseriesChartProps {
  data: TimeseriesPoint[];
}

export function TimeseriesChart({ data }: TimeseriesChartProps) {
  if (data.length === 0) {
    return <p className="text-gray-500 text-sm">No timeseries data available</p>;
  }

  // Prepare data for the chart
  const chartData = data.map((point) => ({
    year: point.year,
    happiness: point.happiness,
    trust: point.trust * 10, // Scale trust to 0-10 for better visualization
    life_satisfaction: point.life_satisfaction,
  }));

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis domain={[0, 10]} />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="happiness"
            stroke="#3b82f6"
            strokeWidth={2}
            name="Happiness"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="trust"
            stroke="#8b5cf6"
            strokeWidth={2}
            name="Trust (×10)"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="life_satisfaction"
            stroke="#10b981"
            strokeWidth={2}
            name="Life Satisfaction"
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
