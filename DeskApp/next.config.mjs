/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {},
  
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        crypto: false,
        os: false,
        util: false,
        stream: false,
        'electron-store': false,
        electron: false,
      };
      
      // Exclude Node.js modules from browser bundle
      config.externals = config.externals || [];
      config.externals.push({
        'electron': 'commonjs electron',
        'electron-store': 'commonjs electron-store',
      });
    }
    return config;
  },
}

export default nextConfig;