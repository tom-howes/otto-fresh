import { type NextRequest } from "next/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://backend-service-484671782718.us-east1.run.app";

export async function streamProxy(req: NextRequest, path: string) {
  const body = await req.json();
  const cookie = req.headers.get("cookie") ?? "";

  const backendRes = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", cookie },
    body: JSON.stringify(body),
  });

  return new Response(backendRes.body, {
    status: backendRes.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}