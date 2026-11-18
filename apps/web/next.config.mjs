/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  outputFileTracingRoot: import.meta.dirname,
  reactStrictMode: true,
  async headers() {
    const privateHeaders = [
      { key: "Referrer-Policy", value: "no-referrer" },
      { key: "X-Robots-Tag", value: "noindex, nofollow" },
    ];
    return [
      { source: "/lista/:path*", headers: privateHeaders },
      { source: "/mi-lista", headers: privateHeaders },
    ];
  },
};

export default nextConfig;
