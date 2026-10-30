import type { Metadata, Viewport } from "next";
import "@fontsource/public-sans/400.css";
import "@fontsource/public-sans/500.css";
import "@fontsource/public-sans/600.css";
import "@fontsource/public-sans/700.css";
import "@fontsource/sora/600.css";
import "@fontsource/sora/700.css";
import "./globals.css";

import { DemoBanner } from "@/components/layout/demo-banner";
import { Providers } from "@/lib/providers";

export const metadata: Metadata = {
  title: {
    default: "APAAR-SDMV · Student Data Platform",
    template: "%s · APAAR-SDMV",
  },
  description:
    "Student Data Management & Verification Platform prototype. Synthetic data only; all external integrations are mock/sandbox.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0B1F33",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-dvh antialiased">
        <DemoBanner />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
