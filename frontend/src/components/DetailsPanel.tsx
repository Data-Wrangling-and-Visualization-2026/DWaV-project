import { useEffect } from 'react';
import { useStore } from '../store';
import { api } from '../services/api';
import { TimeseriesChart } from './TimeseriesChart';

export function DetailsPanel() {
  const { selectedPoint, timeseries, setTimeseries, setLoading } = useStore();

  // Fetch timeseries when a country is selected
  useEffect(() => {
    if (selectedPoint) {
      const fetchTimeseries = async () => {
        setLoading(true);
        try {
          const data = await api.getTimeseries(selectedPoint.country);
          setTimeseries(data);
        } catch (err) {
          console.error('Failed to fetch timeseries:', err);
          setTimeseries([]);
        } finally {
          setLoading(false);
        }
      };

      fetchTimeseries();
    } else {
      setTimeseries([]);
    }
  }, [selectedPoint, setTimeseries, setLoading]);

  if (!selectedPoint) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg h-full flex items-center justify-center">
        <p className="text-gray-500 text-center">
          Click on a point in the 3D visualization to see details
        </p>
      </div>
    );
  }

  const { country, region, year, values } = selectedPoint;

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">{country}</h2>
        <div className="flex gap-4 text-sm text-gray-600">
          <span>
            <strong>Region:</strong> {region}
          </span>
          <span>
            <strong>Year:</strong> {year}
          </span>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-3">Values</h3>
        <div className="space-y-2">
          <ValueBar label="Happiness" value={values.happiness} max={10} color="blue" />
          <ValueBar label="Life Satisfaction" value={values.life_satisfaction} max={10} color="green" />
          <ValueBar label="Trust" value={values.trust} max={1} color="purple" />
          <ValueBar label="Religiosity" value={values.religiosity} max={1} color="orange" />
          <ValueBar label="Political Orientation" value={values.political_orientation} max={1} color="red" />
          <ValueBar label="Moral Values" value={values.moral_values} max={1} color="indigo" />
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-3">3D Position</h3>
        <div className="text-sm text-gray-600 space-y-1">
          <p>
            <strong>X:</strong> {selectedPoint.embedding.x.toFixed(3)}
          </p>
          <p>
            <strong>Y:</strong> {selectedPoint.embedding.y.toFixed(3)}
          </p>
          <p>
            <strong>Z:</strong> {selectedPoint.embedding.z.toFixed(3)}
          </p>
        </div>
      </div>

      {timeseries.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-3">
            {country} Over Time
          </h3>
          <TimeseriesChart data={timeseries} />
        </div>
      )}
    </div>
  );
}

interface ValueBarProps {
  label: string;
  value: number;
  max: number;
  color: string;
}

function ValueBar({ label, value, max, color }: ValueBarProps) {
  const percentage = (value / max) * 100;
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
    indigo: 'bg-indigo-500',
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="text-gray-600 font-medium">{value.toFixed(2)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${colorClasses[color as keyof typeof colorClasses]} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
