export default function Loading() {
    return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-black">
            <div className="w-full max-w-5xl px-6">
                <div className="animate-pulse rounded-xl h-[500px] w-full bg-zinc-200 dark:bg-zinc-800 shadow-inner" />
            </div>
        </div>
    );
}