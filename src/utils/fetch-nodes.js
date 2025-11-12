export async function fetchNodes() {
    const metaRes = await fetch("http://localhost:8000/locations");

    return await metaRes.json();
}