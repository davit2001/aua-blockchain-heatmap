import { fetchNodes } from "../utils/fetch-nodes";
import Heatmap from "@/components/Heatmap";

export default async function Home() {
  const data = await fetchNodes();
  console.log('data', data)
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <Heatmap data={data} />
    </div>
  );
}
