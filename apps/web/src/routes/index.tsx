import { createFileRoute } from "@tanstack/react-router";
import { PipelineBuilder } from "@/pipeline/components/PipelineBuilder";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "FlowWeaver — Visual Preprocessing Platform" },
      { name: "description", content: "A visual, node-based builder for preprocessing and cleaning AI datasets. Drag, connect, and compile pipelines on an infinite canvas." },
      { property: "og:title", content: "FlowWeaver — Visual Preprocessing Platform" },
      { property: "og:description", content: "A visual, node-based builder for preprocessing and cleaning AI datasets." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  return <PipelineBuilder />;
}
