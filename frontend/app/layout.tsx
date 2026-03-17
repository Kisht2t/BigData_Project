import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MARS — Multi-Agent Research Synthesizer",
  description:
    "Ask complex tech and science questions. Three specialized agents retrieve, cross-validate, and synthesize answers from arXiv, Hacker News, and GitHub.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
