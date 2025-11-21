// Fetch Bitcoin node locations from the API
export async function fetchNodes() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  
  try {
    const response = await fetch(`${apiUrl}/locations`, {
      next: { revalidate: 60 }, // Revalidate every 60 seconds
    });
    
    if (!response.ok) {
      console.error(`Failed to fetch nodes: ${response.status} ${response.statusText}`);
      return [];
    }
    
    const data = await response.json();
    
    // Handle both formats: direct array or { locations: array }
    if (Array.isArray(data)) {
      console.log(`✅ Loaded ${data.length} Bitcoin testnet peer locations`);
      return data;
    } else if (data.locations && Array.isArray(data.locations)) {
      console.log(`✅ Loaded ${data.locations.length} Bitcoin testnet peer locations`);
      return data.locations;
    }
    
    console.error('Invalid data format from API:', data);
    return [];
  } catch (error) {
    console.error("Error fetching node locations:", error);
    return [];
  }
}

