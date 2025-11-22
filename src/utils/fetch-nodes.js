export async function fetchNodes() {
    try {
        const metaRes = await fetch("http://localhost:8000/locations");

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
        const metaRes = await fetch("http://localhost:8000/stats");

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