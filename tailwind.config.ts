import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A0A0A",
        "ink-soft": "#1A1A1A",
        muted: "#595959",
        rule: "#E5E0D6",
        cream: "#F8F6F1",
        "cream-deep": "#EFEBE1",
        teal: {
          DEFAULT: "#0E5E5E",
          deep: "#0A4848",
        },
        amber: {
          DEFAULT: "#B45309",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui"],
        display: ["var(--font-fraunces)", "ui-serif", "Georgia"],
      },
      fontFeatureSettings: {
        tnum: '"tnum"',
      },
      letterSpacing: {
        tightest: "-0.04em",
        "extra-tight": "-0.025em",
      },
      maxWidth: {
        container: "1240px",
      },
    },
  },
  plugins: [],
};
export default config;
