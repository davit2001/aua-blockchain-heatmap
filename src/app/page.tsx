import { fetchNodes } from "../utils/fetch-nodes";
import Heatmap from "@/components/Heatmap";

export default async function Home() {
  try {
    const data = await fetchNodes();
    
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
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <Heatmap data={data} />
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
