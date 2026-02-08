import { useEffect, useMemo } from 'react';
import { useStore } from '../store';
import { api } from '../services/api';

export function Filters() {
  const { data, filters, setFilters, setData, setLoading, setError } = useStore();

  // Extract unique values from current data
  const years = useMemo(() => {
    const yearSet = new Set(data.map((d) => d.year));
    return Array.from(yearSet).sort((a, b) => b - a);
  }, [data]);

  const regions = useMemo(() => {
    const regionSet = new Set(data.map((d) => d.region));
    return Array.from(regionSet).sort();
  }, [data]);

  const countries = useMemo(() => {
    const countrySet = new Set(data.map((d) => d.country));
    return Array.from(countrySet).sort();
  }, [data]);

  // Fetch data when filters change (including initial load)
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const newData = await api.getData(filters);
        setData(newData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [filters, setData, setLoading, setError]);

  return (
    <div className="bg-white p-4 rounded-lg shadow-lg space-y-4">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Filters</h2>

      {/* Year Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Year: {filters.year || 'All'}
        </label>
        <select
          value={filters.year || ''}
          onChange={(e) =>
            setFilters({ year: e.target.value ? parseInt(e.target.value) : undefined })
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Years</option>
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>

      {/* Region Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Region</label>
        <select
          value={filters.region || ''}
          onChange={(e) => setFilters({ region: e.target.value || undefined })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Regions</option>
          {regions.map((region) => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
      </div>

      {/* Country Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Country</label>
        <select
          value={filters.country || ''}
          onChange={(e) => setFilters({ country: e.target.value || undefined })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Countries</option>
          {countries.map((country) => (
            <option key={country} value={country}>
              {country}
            </option>
          ))}
        </select>
      </div>

      {/* Data Count */}
      <div className="pt-2 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Showing <span className="font-semibold">{data.length}</span> data points
        </p>
      </div>
    </div>
  );
}
