import { useEffect, useState } from 'react';
import { api } from '../services/api';

export function ConnectionTest() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const testConnection = async () => {
      try {
        const result = await api.healthCheck();
        setStatus('connected');
        setMessage(`Backend connected: ${result.status}`);
      } catch (error) {
        setStatus('error');
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setMessage(errorMessage);
      }
    };

    testConnection();
  }, []);

  if (status === 'checking') {
    return (
      <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 px-4 py-3 mx-4 mt-4">
        <p className="font-medium">Testing backend connection...</p>
      </div>
    );
  }

  if (status === 'connected') {
    return (
      <div className="bg-green-100 border-l-4 border-green-500 text-green-700 px-4 py-3 mx-4 mt-4">
        <p className="font-medium">✓ {message}</p>
      </div>
    );
  }

  return (
    <div className="bg-red-100 border-l-4 border-red-500 text-red-700 px-4 py-3 mx-4 mt-4">
      <p className="font-medium">✗ Backend Connection Failed</p>
      <p className="text-sm mt-1">{message}</p>
      <p className="text-sm mt-2">
        <strong>Possible solutions:</strong>
      </p>
      <ul className="text-sm mt-1 list-disc list-inside">
        <li>Make sure your backend is running at http://localhost:8000</li>
        <li>Check if CORS is enabled in your FastAPI backend</li>
        <li>Open browser console (F12) for more details</li>
      </ul>
    </div>
  );
}
