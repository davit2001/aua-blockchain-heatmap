interface StatCardSkeletonProps {
    variant?: "blue" | "green" | "purple"
    className?: string
}

export default function StatCardSkeleton({ variant = "blue" }: StatCardSkeletonProps) {
    const bgColors = {
        blue: "rgba(23, 37, 84, 0.8)",
        green: "rgba(2, 44, 34, 0.8)",
        purple: "rgba(46, 16, 101, 0.8)",
    }

    const borderColors = {
        blue: "rgba(30, 58, 138, 0.5)",
        green: "rgba(6, 95, 70, 0.5)",
        purple: "rgba(88, 28, 135, 0.5)",
    }

    const shimmerColors = {
        blue: "rgba(30, 64, 175, 0.3)",
        green: "rgba(6, 78, 59, 0.3)",
        purple: "rgba(107, 33, 168, 0.3)",
    }

    return (
        <div
            style={{
                borderRadius: "0.75rem",
                borderWidth: "1px",
                borderStyle: "solid",
                borderColor: borderColors[variant],
                padding: "2rem",
                backgroundColor: bgColors[variant],
                backdropFilter: "blur(4px)",
                animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
            }}
        >
            <div
                style={{
                    height: "3rem",
                    width: "8rem",
                    borderRadius: "0.5rem",
                    marginBottom: "0.5rem",
                    backgroundColor: shimmerColors[variant],
                }}
            ></div>

            <div
                style={{
                    height: "1.5rem",
                    width: "6rem",
                    borderRadius: "0.5rem",
                    backgroundColor: shimmerColors[variant],
                }}
            ></div>
        </div>
    )
}