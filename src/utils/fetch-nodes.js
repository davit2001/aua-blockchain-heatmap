const API_URL = process.env.API_URL || "http://localhost:8000";

export async function fetchNodes() {
    try {
        const metaRes = await fetch(`${API_URL}/locations`);

        const data = await metaRes.json();

        return {
            data: data,
            error: null,
        }
    } catch (error) {
        return {
            data: null,
            error: error.message,
        }
    }
}

export async function fetchCrawlersMetadata() {
    try {
        const metaRes = await fetch(`${API_URL}/stats`);

        const data = await metaRes.json();

        return {
            data: data,
            error: null,
        }
    } catch (error) {
        return {
            data: null,
            error: error.message,
        }
    }
}