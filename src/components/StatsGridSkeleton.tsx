import StatCardSkeleton from "./StatCardSkeleton"

export default function StatsGridSkeleton() {
    return (
        <>
            <style>
                {`
                    @media (min-width: 768px) {
                        .stats-grid-skeleton {
                            grid-template-columns: repeat(3, 1fr);
                        }
                    }
                `}
            </style>

            <div
                className="stats-grid-skeleton"
                style={{
                    display: "grid",
                    gridTemplateColumns: "1fr",
                    gap: "1.5rem",
                }}
            >
                <StatCardSkeleton variant="blue" />
                <StatCardSkeleton variant="green" />
                <StatCardSkeleton variant="purple" />
            </div>
        </>
    )
}