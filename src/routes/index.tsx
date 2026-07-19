import { createFileRoute } from "@tanstack/react-router";
import { PipelineBuilder } from "@/pipeline/components/PipelineBuilder";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Flowline — Visual Pipeline Builder" },
      { name: "description", content: "A visual, node-based builder for designing data pipelines. Drag, connect, and simulate runs on an infinite canvas." },
      { property: "og:title", content: "Flowline — Visual Pipeline Builder" },
      { property: "og:description", content: "A visual, node-based builder for designing data pipelines." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  return <PipelineBuilder />;
}
