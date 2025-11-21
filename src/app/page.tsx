import { fetchNodes } from "../utils/fetch-nodes";
import Heatmap from "@/components/Heatmap";

async function fetchStats() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}/stats`, {
      next: { revalidate: 60 },
    });
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error("Failed to fetch stats:", error);
  }
  return null;
}

export default async function Home() {
  try {
    const [data, stats] = await Promise.all([
      fetchNodes(),
      fetchStats()
    ]);
    
    // Log data only in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Fetched node data:', data?.length || 0, 'locations');
    }
    
    // Validate data
    if (!data || !Array.isArray(data)) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
          <div className="text-center p-8">
            <h2 className="text-xl font-semibold mb-4">Invalid Data Format</h2>
            <p className="text-gray-600 dark:text-gray-400">
              The API returned unexpected data. Please check the backend service.
            </p>
          </div>
        </div>
      );
    }
    
    if (data.length === 0) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
          <div className="text-center p-8">
            <h2 className="text-xl font-semibold mb-4">No Node Data Available</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              No Bitcoin nodes have been discovered yet.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Run the crawler to discover nodes: <code className="bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded">python crawler.py</code>
            </p>
          </div>
        </div>
      );
    }
    
    return (
      <div className="min-h-screen bg-zinc-50 font-sans dark:bg-black p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header with Stats */}
          <div className="mb-6 text-center">
            <h1 className="text-4xl font-bold mb-4 text-gray-900 dark:text-white">
              Bitcoin Testnet Node Heatmap
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Real-time visualization of Bitcoin testnet peer distribution
            </p>
            {stats && (
              <div className="flex justify-center gap-6 text-sm">
                <div className="bg-white dark:bg-gray-800 px-6 py-3 rounded-lg shadow">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {stats.total_peers?.toLocaleString() || 0}
                  </div>
                  <div className="text-gray-600 dark:text-gray-400">Total Peers</div>
                </div>
                <div className="bg-white dark:bg-gray-800 px-6 py-3 rounded-lg shadow">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {stats.geolocated_peers?.toLocaleString() || 0}
                  </div>
                  <div className="text-gray-600 dark:text-gray-400">Geolocated</div>
                </div>
                <div className="bg-white dark:bg-gray-800 px-6 py-3 rounded-lg shadow">
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {stats.countries || 0}
                  </div>
                  <div className="text-gray-600 dark:text-gray-400">Countries</div>
                </div>
              </div>
            )}
          </div>
          
          {/* Heatmap */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden" style={{ height: '600px' }}>
            <Heatmap data={data} />
          </div>
          
          {/* Footer Info */}
          <div className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>Data collected from real Bitcoin Core testnet P2P network crawling</p>
            <p className="mt-1">Network: <span className="font-mono text-orange-600 dark:text-orange-400">testnet</span></p>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error loading Bitcoin node data:', error);
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <div className="text-center p-8">
          <h2 className="text-xl font-semibold mb-4 text-red-600 dark:text-red-400">Error Loading Data</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Failed to fetch Bitcoin node locations from the API.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            {error instanceof Error ? error.message : 'Unknown error occurred'}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            Make sure the API server is running: <code className="bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded">uvicorn app:app</code>
          </p>
        </div>
      </div>
    );
  }
}
