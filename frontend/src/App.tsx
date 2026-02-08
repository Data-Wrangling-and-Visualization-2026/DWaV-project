import { Scene3D } from './components/Scene3D';
import { Filters } from './components/Filters';
import { DetailsPanel } from './components/DetailsPanel';
import { ConnectionTest } from './components/ConnectionTest';
import { useStore } from './store';

function App() {
  const { error, isLoading } = useStore();

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-800">WVS Values Explorer</h1>
        <p className="text-sm text-gray-600">World Values Survey Data Visualization</p>
      </header>

      {/* Connection Test */}
      <ConnectionTest />

      {/* Error Banner */}
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 px-4 py-3 mx-4 mt-4">
          <p className="font-medium">Error: {error}</p>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 px-4 py-3 mx-4 mt-4">
          <p className="font-medium">Loading data...</p>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left Sidebar - Filters */}
        <div className="w-64 flex-shrink-0">
          <Filters />
        </div>

        {/* Center - 3D Visualization */}
        <div className="flex-1 rounded-lg overflow-hidden shadow-lg">
          <Scene3D />
        </div>

        {/* Right Sidebar - Details Panel */}
        <div className="w-96 flex-shrink-0">
          <DetailsPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
