import { StatCard } from "@/components/StatCard"

interface Stat {
    value: string | number
    label: string
    variant?: "blue" | "green" | "purple"
}

interface StatsGridProps {
    stats: Stat[]
}

export function StatsGrid({ stats }: StatsGridProps) {
    return (
        <>
            <style>
                {`
                    @media (min-width: 768px) {
                        .stats-grid-responsive {
                            grid-template-columns: repeat(3, 1fr);
                        }
                    }
                `}
            </style>

            <div
                className="stats-grid-responsive"
                style={{
                    display: "flex",
                    gap: "1.5rem", // gap-6
                }}
            >
                {stats.map((stat, index) => (
                    <StatCard
                        key={index}
                        value={stat.value}
                        label={stat.label}
                        variant={stat.variant}
                    />
                ))}
            </div>
        </>
    )
}