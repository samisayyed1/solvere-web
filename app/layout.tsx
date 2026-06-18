import type { Metadata } from "next";
import { Inter, Fraunces } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-fraunces",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Solvere — Healthcare Claim Recovery for the UAE",
  description:
    "Solvere recovers denied healthcare insurance claims for UAE clinics. AI-native, pay-only-on-recovery. Abu Dhabi-based.",
  openGraph: {
    title: "Solvere",
    description:
      "A new standard for UAE claim recovery. AI agents plus a DHA-licensed coder, pay only on recovery.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`}>
      <body className="font-sans antialiased bg-cream text-ink-soft">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:bg-ink focus:text-cream focus:px-4 focus:py-2 focus:z-50 focus:rounded"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
