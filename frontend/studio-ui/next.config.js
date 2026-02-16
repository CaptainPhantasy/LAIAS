/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  transpilePackages: ['../shared'],
  experimental: {
    // Enable optimizations
    optimizePackageImports: ['lucide-react', '@monaco-editor/react'],
  },
  env: {
    NEXT_PUBLIC_AGENT_GENERATOR_URL: process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:8001',
    NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL: process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:8002',
  },
  async rewrites() {
    return [
      {
        source: '/api/agent-generator/:path*',
        destination: `${process.env.NEXT_PUBLIC_AGENT_GENERATOR_URL || 'http://localhost:8001'}/api/:path*`,
      },
      {
        source: '/api/docker-orchestrator/:path*',
        destination: `${process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:8002'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
