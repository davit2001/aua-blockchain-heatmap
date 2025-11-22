interface StatCardProps {
    value: string | number
    label: string
    variant?: "blue" | "green" | "purple"
    className?: string
}

export function StatCard({ value, label, variant = "blue" }: StatCardProps) {
    const bgColors = {
        blue: "rgba(23, 37, 84)",
        green: "rgba(2, 44, 34)",
        purple: "rgba(46, 16, 101)",
    }

    const borderColors = {
        blue: "rgba(30, 58, 138)",
        green: "rgba(6, 95, 70)",
        purple: "rgba(88, 28, 135)",
    }

    const valueColors = {
        blue: "#60A5FA",
        green: "#34D399",
        purple: "#C084FC",
    }

    return (
        <div
            style={{
                flex: 1,
                borderRadius: "0.75rem",
                borderWidth: "1px",
                borderStyle: "solid",
                borderColor: borderColors[variant],
                padding: "2rem",
                backgroundColor: bgColors[variant],
                backdropFilter: "blur(4px)",
            }}
        >
            <div
                style={{
                    fontSize: "3rem",
                    fontWeight: 700,
                    marginBottom: "0.5rem",
                    color: valueColors[variant],
                }}
            >
                {value.toLocaleString()}
            </div>

            <div
                style={{
                    color: "#9CA3AF",
                    fontSize: "1.125rem",
                }}
            >
                {label}
            </div>
        </div>
    )
}