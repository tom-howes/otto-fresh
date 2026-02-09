import { Backlog } from "@/components/backlog";
import { type Metadata } from "next";

export const metadata: Metadata = {
  title: "Backlog",
};

const BacklogPage = () => {
  return <Backlog />;
};

export default BacklogPage;