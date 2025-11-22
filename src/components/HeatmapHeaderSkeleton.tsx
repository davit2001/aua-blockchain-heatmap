import StatsGridSkeleton from './StatsGridSkeleton';

export default function HeatmapHeaderSkeleton() {
    return (
        <>
            <div
                style={{
                    marginBottom: "3rem",
                    animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                }}
            >
                <div
                    style={{
                        height: "4rem",
                        width: "75%",
                        backgroundColor: "rgba(55, 65, 81, 0.5)",
                        borderRadius: "0.5rem",
                        marginBottom: "1rem",
                    }}
                ></div>

                <div
                    style={{
                        height: "2rem",
                        width: "50%",
                        backgroundColor: "rgba(55, 65, 81, 0.5)",
                        borderRadius: "0.5rem",
                    }}
                ></div>
            </div>

            <StatsGridSkeleton />
        </>
    )
}