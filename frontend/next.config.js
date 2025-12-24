/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // API routes will proxy to Python backend
  async rewrites() {
    return [
      {
        source: '/api/subscriptions',
        destination: 'http://localhost:8000/api/subscriptions',
      },
    ];
  },
};

module.exports = nextConfig;








