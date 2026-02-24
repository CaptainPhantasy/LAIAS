/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  experimental: {
    // Enable optimizations
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  env: {
    NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL: process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:4522',
  },
};

module.exports = nextConfig;
