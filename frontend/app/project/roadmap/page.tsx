import { type Metadata } from "next";
import { Roadmap } from "@/components/roadmap";

export const metadata: Metadata = {
  title: "Roadmap",
};

const RoadmapPage = () => {
  return <Roadmap />;
};

export default RoadmapPage;