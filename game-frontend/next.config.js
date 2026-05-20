/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  swcMinify: false,
  output: 'export',
  distDir: 'dist',
  images: {
    unoptimized: true,
    domains: ['images.meshy.ai', 'cdn.meshy.ai'],
  },
  env: {
    NEXT_PUBLIC_MESHY_API_KEY: process.env.NEXT_PUBLIC_MESHY_API_KEY,
    NEXT_PUBLIC_CIRCLE_APP_ID: process.env.NEXT_PUBLIC_CIRCLE_APP_ID,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8080',
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001',
  },
};

module.exports = nextConfig;
