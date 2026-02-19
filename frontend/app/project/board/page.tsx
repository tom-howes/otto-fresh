import { Board } from "@/components/board";
import { type Metadata } from "next";

export const metadata: Metadata = {
  title: "Board",
};

const BoardPage = () => {
  return <Board />;
};

export default BoardPage;