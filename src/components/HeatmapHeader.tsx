import { StatsGrid } from "@/components/StatsGrid";
import { fetchCrawlersMetadata } from "@/utils/fetch-nodes";

interface HeatmapHeaderProps {
    title: string;
    subtitle: string;
}

export default async function HeatmapHeader({ title, subtitle }: HeatmapHeaderProps) {
    const { data } = await fetchCrawlersMetadata();

    return (
        <div
            style={{
                maxWidth: "1200px",
                margin: "0 auto 40px",
            }}
        >
            <div style={{ marginBottom: "24px" }}>
                <h1
                    style={{
                        fontSize: "2.5rem",
                        lineHeight: "1",
                        fontWeight: 700,
                        marginBottom: "1rem",
                        textWrap: "balance",
                    }}
                >
                    {title}
                </h1>

                <p
                    style={{
                        color: "#9CA3AF",
                        fontSize: "1.25rem",
                    }}
                >
                    {subtitle}
                </p>
            </div>

            <StatsGrid
                stats={[
                    { label: "Total Peers", value: data.total_peers, variant: "blue" },
                    { label: "Geolocated Peers", value: data.geolocated_peers, variant: "green" },
                    { label: "Crawl duration", value: data.crawl_duration, variant: "purple" },
                ]}
            />
        </div>
    );
}
