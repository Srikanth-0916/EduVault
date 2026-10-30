import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "APAAR-SDMV",
  description:
    "Student Data Management & Verification Platform prototype. Synthetic data only; mock integrations.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-dvh antialiased">
        {/* Persistent demo/mock ribbon (plan global constraint) */}
        <div
          role="note"
          className="bg-amber-600 px-4 py-2 text-center text-xs font-medium tracking-wide text-white"
        >
          Synthetic demo data · Mock integrations
        </div>
        {children}
      </body>
    </html>
  );
}
