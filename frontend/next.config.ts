import type { NextConfig } from "next";

// Conditionally import Sentry only if available
let withSentryConfig: any = null;
try {
  const sentry = require("@sentry/nextjs");
  withSentryConfig = sentry.withSentryConfig;
} catch (e) {
  // Sentry not installed, use identity function
  withSentryConfig = (config: any, ...args: any[]) => config;
}

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  // Disable Turbopack - use webpack for Sentry compatibility
  // Turbopack doesn't fully support Sentry yet
  // This will be used when --webpack flag is passed
  webpack: (config, { isServer }) => {
    return config;
  },
  // Add empty turbopack config to silence the error
  // But we'll use --webpack flag to force webpack usage
  turbopack: {},
  // CDN and static asset optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60,
  },
  // Compress static assets
  compress: true,
  // Static asset caching
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/_next/image/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

// Export config with Sentry (if available)
export default withSentryConfig(
  nextConfig,
  {
    // For all available options, see:
    // https://github.com/getsentry/sentry-webpack-plugin#options

    // Suppresses source map uploading logs during build
    silent: true,
    org: process.env.SENTRY_ORG,
    project: process.env.SENTRY_PROJECT,
    
    // Only upload source maps in production
    widenClientFileUpload: true,
    hideSourceMaps: true,
    disableLogger: true,
  },
  {
    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    automaticVercelMonitors: true,
  }
) || nextConfig;
