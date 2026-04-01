import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://backend-service-484671782718.us-east1.run.app/:path*",
      },
    ];
  },
};

export default nextConfig;