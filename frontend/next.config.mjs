/** @type {import("next").NextConfig} */
const config = {
  reactStrictMode: true,
  eslint: {
    // Ignore ESLint errors during builds (for UI development)
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Ignore TypeScript errors during builds (for UI development)
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
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.clerk.dev',
      },
      {
        protocol: 'https',
        hostname: 'www.gravatar.com',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',
      },
      {
        protocol: 'https',
        hostname: 'img.clerk.com',
      },
      {
        protocol: 'https',
        hostname: 'i.pravatar.cc',
      },
      {
        protocol: 'https',
        hostname: 'cdn.worldvectorlogo.com',
      },
    ],
  },
};

export default config;