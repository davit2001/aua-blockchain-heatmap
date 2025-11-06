export async function normalizeBitcoinNodes() {
    const metaRes = await fetch("https://bitnodes.io/api/v1/snapshots/latest/");
    const data = await metaRes.json();
    const nodes = Object.entries(data.nodes);
    return nodes
        .map(([ip, values]) => ({
            ip_port: ip,
            version: values[0],
            user_agent: values[1],
            timestamp: values[2],
            ping: values[3],
            block_height: values[4],
            hostname: values[5],
            city: values[6],
            country: values[7],
            latitude: values[8],
            longitude: values[9],
            timezone: values[10],
            asn: values[11],
            isp: values[12],
        }))
        .filter(n => n.latitude && n.longitude && n.latitude !== 0 && n.longitude !== 0);
}