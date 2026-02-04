/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    turbo: {
      resolveAlias: {
        // Force absolute paths
      }
    }
  }
}

export default nextConfig