/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
    PROJECT_NAME: process.env.NEXT_PUBLIC_PROJECT_NAME || 'Komornicka 100',
  },
  // We'll use the API_URL from environment variables passed from docker-compose
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
  // Ensure React Hook Form works with SSR
  webpack: (config) => {
    return config;
  },
}

module.exports = nextConfig