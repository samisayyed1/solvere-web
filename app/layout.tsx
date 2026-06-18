import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Self-hosted .woff2 per docs/BRIEF.md §3 (no Google Fonts CDN — affects LCP).
// adjustFontFallback pins the metric-matched fallback to minimize CLS while
// Fraunces / Inter swap in.
//
// Preload only the weights needed above the fold (Fraunces 500 for the LCP
// h1, Inter 400 + 500 for subhead + button). The remaining weights ship in
// the same CSS variable but defer their <link rel=preload>, so the critical
// path isn't fighting six fonts at once.
const frauncesCritical = localFont({
  src: [{ path: "../public/fonts/Fraunces-500.woff2", weight: "500", style: "normal" }],
  variable: "--font-fraunces",
  display: "swap",
  preload: true,
  adjustFontFallback: "Times New Roman",
  fallback: ["Georgia", "serif"],
});

// Secondary Fraunces weights — same CSS variable, but no preload tag, so they
// load when first painted, not on the critical path.
const frauncesRest = localFont({
  src: [
    { path: "../public/fonts/Fraunces-400.woff2", weight: "400", style: "normal" },
    { path: "../public/fonts/Fraunces-700.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-fraunces-rest",
  display: "swap",
  preload: false,
  adjustFontFallback: "Times New Roman",
  fallback: ["Georgia", "serif"],
});

const interCritical = localFont({
  src: [
    { path: "../public/fonts/Inter-400.woff2", weight: "400", style: "normal" },
    { path: "../public/fonts/Inter-500.woff2", weight: "500", style: "normal" },
    // Inter 700 is the LCP weight on the new hero — preload eagerly.
    { path: "../public/fonts/Inter-700.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-inter",
  display: "swap",
  preload: true,
  adjustFontFallback: "Arial",
  fallback: ["system-ui", "sans-serif"],
});

const interRest = localFont({
  src: [{ path: "../public/fonts/Inter-600.woff2", weight: "600", style: "normal" }],
  variable: "--font-inter-rest",
  display: "swap",
  preload: false,
  adjustFontFallback: "Arial",
  fallback: ["system-ui", "sans-serif"],
});

// Viewport must be its own export in Next 14+ (separated from metadata).
export const viewport: Viewport = {
  themeColor: "#F8F6F1",
  width: "device-width",
  initialScale: 1,
};

// SEO + Open Graph per docs/BRIEF.md §12 — copy locked in docs/COPY.md §8.
export const metadata: Metadata = {
  metadataBase: new URL("https://solvere.ai"),
  title: "Solvere — Healthcare Claim Recovery for the UAE",
  description:
    "Solvere recovers denied healthcare insurance claims for UAE clinics. AI-native, pay-only-on-recovery. Abu Dhabi-based.",
  alternates: { canonical: "https://solvere.ai" },
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    url: "https://solvere.ai",
    title: "Solvere — Healthcare Claim Recovery for the UAE",
    description:
      "Recover the denied insurance claims your billers gave up on. AI-native. Pay only on recovery.",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "Solvere" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Solvere — Healthcare Claim Recovery for the UAE",
    description:
      "Recover the denied insurance claims your billers gave up on. AI-native. Pay only on recovery.",
    images: ["/og.png"],
  },
  icons: {
    icon: [
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon-16.png", sizes: "16x16", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${frauncesCritical.variable} ${frauncesRest.variable} ${interCritical.variable} ${interRest.variable}`}
    >
      <body className="bg-cream text-ink-soft antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:bg-cream focus:px-3 focus:py-2 focus:text-ink"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
