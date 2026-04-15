/** @type {import("next").NextConfig} */
const config = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  redirects: async () => {
    return [
      {
        source: "/project",
        destination: "/project/backlog",
        permanent: true,
      },
      {
        source: "/",
        destination: "/project/backlog",
        permanent: true,
      },
    ];
  },

  // ── Proxy /api/* → backend so session_token cookie works same-origin ──
  rewrites: async () => {
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

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.clerk.dev" },
      { protocol: "https", hostname: "www.gravatar.com" },
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
      { protocol: "https", hostname: "img.clerk.com" },
      { protocol: "https", hostname: "i.pravatar.cc" },
      { protocol: "https", hostname: "cdn.worldvectorlogo.com" },
    ],
  },
};

export default config;