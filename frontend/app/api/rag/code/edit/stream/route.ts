import { type NextRequest } from "next/server";
import { streamProxy } from "@/app/api/stream-proxy";
export const POST = (req: NextRequest) => streamProxy(req, "/rag/code/edit/stream");