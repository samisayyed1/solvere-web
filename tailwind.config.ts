import type { Config } from "tailwindcss";

// Solvere design tokens — sourced verbatim from docs/DESIGN.md §6.1, §6.3, §6.4.
// Do not introduce values not listed here. The palette is nine colors. Two fonts.
// The spacing scale is the 8pt grid. Type scale is responsive (mobile → desktop).

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    // Replace the default palette wholesale — only the nine locked tokens exist.
    colors: {
      transparent: "transparent",
      current: "currentColor",
      ink: "#0A0A0A",
      "ink-soft": "#1A1A1A",
      muted: "#595959",
      rule: "#E5E0D6",
      cream: "#F8F6F1",
      "cream-deep": "#EFEBE1",
      teal: "#0E5E5E",
      "teal-deep": "#0A4848",
      amber: "#B45309",
    },
    fontFamily: {
      // Wired up in app/layout.tsx via next/font/local with CSS variables.
      display: ["var(--font-fraunces)", "Georgia", "serif"],
      sans: ["var(--font-inter)", "system-ui", "sans-serif"],
    },
    // Spacing replaced wholesale — 8pt grid only. No arbitrary values.
    spacing: {
      0: "0px",
      px: "1px",
      1: "8px",
      2: "16px",
      3: "24px",
      4: "32px",
      5: "48px",
      6: "64px",
      7: "96px",
      8: "128px",
      9: "192px",
    },
    borderRadius: {
      none: "0",
      sm: "4px",
      md: "6px",
      lg: "8px",
      xl: "12px", // §14 — never exceed 12px
    },
    screens: {
      sm: "640px",
      md: "1024px",
      lg: "1440px",
    },
    extend: {
      maxWidth: {
        prose: "640px",   // body text column cap
        content: "1140px", // site content cap
        hero: "960px",
        narrow: "720px",
      },
      // Responsive type scale per §6.3. Format: [size, { lineHeight, letterSpacing, fontWeight }]
      fontSize: {
        // mobile
        "display-m": ["48px", { lineHeight: "1.02", letterSpacing: "-0.02em", fontWeight: "500" }],
        "h1-m": ["36px", { lineHeight: "1.08", letterSpacing: "-0.015em", fontWeight: "500" }],
        "h2-m": ["28px", { lineHeight: "1.15", letterSpacing: "-0.01em", fontWeight: "500" }],
        "h3-m": ["22px", { lineHeight: "1.3", letterSpacing: "-0.005em", fontWeight: "600" }],
        "stat-m": ["72px", { lineHeight: "1", letterSpacing: "-0.03em", fontWeight: "500" }],
        "body-lg-m": ["18px", { lineHeight: "1.5", letterSpacing: "0", fontWeight: "400" }],
        "body-m": ["16px", { lineHeight: "1.55", letterSpacing: "0", fontWeight: "400" }],
        "caption-m": ["13px", { lineHeight: "1.4", letterSpacing: "0.08em", fontWeight: "500" }],
        // desktop
        "display-d": ["88px", { lineHeight: "1.02", letterSpacing: "-0.02em", fontWeight: "500" }],
        "h1-d": ["56px", { lineHeight: "1.08", letterSpacing: "-0.015em", fontWeight: "500" }],
        "h2-d": ["40px", { lineHeight: "1.15", letterSpacing: "-0.01em", fontWeight: "500" }],
        "h3-d": ["26px", { lineHeight: "1.3", letterSpacing: "-0.005em", fontWeight: "600" }],
        "stat-d": ["144px", { lineHeight: "1", letterSpacing: "-0.03em", fontWeight: "500" }],
        "body-lg-d": ["21px", { lineHeight: "1.5", letterSpacing: "0", fontWeight: "400" }],
        "body-d": ["17px", { lineHeight: "1.55", letterSpacing: "0", fontWeight: "400" }],
        "caption-d": ["14px", { lineHeight: "1.4", letterSpacing: "0.08em", fontWeight: "500" }],
      },
      transitionTimingFunction: {
        // §10 — the single allowed scroll/mount easing
        solvere: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
      boxShadow: {
        // §14 — drop shadows never exceed this
        rule: "0 2px 4px rgba(0,0,0,0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
