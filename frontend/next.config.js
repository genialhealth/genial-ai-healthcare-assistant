/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.watchOptions = {
        poll: false,
        aggregateTimeout: 300,
        ignored: ['**/node_modules', '**/.next', '**/.git', '**/docs'],
      };
    }
    return config;
  },
};

module.exports = nextConfig;
