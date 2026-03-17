/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    ORCHESTRATOR_URL: process.env.ORCHESTRATOR_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
