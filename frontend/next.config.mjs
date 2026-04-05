/** @type {import('next').NextConfig} */
const nextConfig = {
  // Production optimizations
  poweredByHeader: false,
  compress: true,

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },

  // Redirect www to apex
  async redirects() {
    return [
      {
        source: "/:path*",
        has: [{ type: "host", value: "www.shieldpay.io" }],
        destination: "https://shieldpay.io/:path*",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
