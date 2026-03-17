import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#f8f9fa",
        card: "#ffffff",
        border: "#e5e7eb",
        muted: "#6b7280",
        accent: {
          blue: "#2563eb",
          green: "#16a34a",
          amber: "#d97706",
          red: "#dc2626",
        },
        source: {
          arxiv: "#1d4ed8",
          hackernews: "#ea580c",
          github: "#1f2937",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        pulse_slow: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
