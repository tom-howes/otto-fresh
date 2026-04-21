import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const backendUrl = 
      process.env.NEXT_PUBLIC_API_URL || 
      "https://backend-service-484671782718.us-east1.run.app";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};
export default nextConfig;