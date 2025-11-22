import { fetchNodes } from "../utils/fetch-nodes";
import Heatmap from "@/components/Heatmap";
import { notFound } from "next/navigation";

export default async function Home() {
  const { data, error } = await fetchNodes();
  if (error) {
    notFound();
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <Heatmap data={data} />
    </div>
  );
}
