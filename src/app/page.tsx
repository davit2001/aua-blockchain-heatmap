import { fetchNodes } from "../utils/fetch-nodes";
import Heatmap from "@/components/Heatmap";
import { notFound } from "next/navigation";
import HeatmapHeader from "@/components/HeatmapHeader";
import HeatmapHeaderSkeleton from "@/components/HeatmapHeaderSkeleton";
import { Suspense } from "react";

export default async function Home() {
    const { data, error } = await fetchNodes();
    if (error) {
        notFound();
    }

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                minHeight: "100vh",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: "sans-serif",
                colorScheme: "dark light",
                marginBottom: "40px",
            }}
        >
            <Suspense fallback={<HeatmapHeaderSkeleton />}>
                <HeatmapHeader
                    title="Bitcoin Testnet Node Heatmap"
                    subtitle="Real-time visualization of Bitcoin testnet peer distribution"
                />
            </Suspense>

            <Heatmap data={data} />
        </div>
    );
}
