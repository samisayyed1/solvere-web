// §7.3 — The Number. Full-width ink band, vertical padding space-9.
// Giant AED 22 Billion stat anchored in a derived breakdown below — turns the
// headline figure from declarative to analytical. Faint ledger-grid background
// (3% cream hairlines, 48px rhythm) suggests a financial document, never loud.

import { FadeIn } from "@/components/FadeIn";

const DERIVED = [
  {
    value: "AED 2.6–3.3B",
    label: "Initially denied annually",
    sub: "12–15% of all UAE healthcare claims",
  },
  {
    value: "60–70%",
    label: "Recoverable on appeal",
    sub: "Industry benchmark on appeal-eligible denials",
  },
  {
    value: "AED 1.6–2.3B",
    label: "Industry-wide leakage",
    sub: "Never recovered. Written off as bad debt.",
  },
];

export function TheNumber() {
  return (
    <section
      aria-label="The Number"
      className="relative bg-ink py-7 md:py-8 border-t border-cream/10 overflow-hidden"
    >
      {/* Ledger grid background — cream hairlines at 3% opacity, 48px rhythm.
          One-stop linear gradient, no decoration beyond rule lines. */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "repeating-linear-gradient(to bottom, transparent 0px, transparent 47px, rgba(248,246,241,0.05) 47px, rgba(248,246,241,0.05) 48px)",
        }}
      />

      <div className="relative mx-auto max-w-content px-3 md:px-5 text-center">
        <FadeIn>
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-cream/55">
            THE OPPORTUNITY
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-3 md:mt-4">
          <p className="font-display text-cream text-stat-m md:text-stat-d">
            AED 22 Billion
          </p>
        </FadeIn>

        <FadeIn delay={0.16} className="mt-3 md:mt-4">
          <p className="mx-auto max-w-[560px] font-sans text-cream/70 text-body-lg-m md:text-body-lg-d">
            paid annually in UAE healthcare claims. A meaningful share is
            denied &mdash; and never recovered. That share is your money.
          </p>
        </FadeIn>

        <FadeIn delay={0.24} className="mt-5">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-cream/55">
            SOURCE &mdash; CBUAE QUARTERLY ECONOMIC REVIEW, REPORTED BY GULF NEWS (2024)
          </p>
        </FadeIn>

        {/* Derived breakdown — anchors the headline 22B in math */}
        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-3 md:divide-x divide-y md:divide-y-0 divide-cream/15 border-t border-cream/15">
          {DERIVED.map((d, i) => (
            <FadeIn key={d.label} delay={0.08 * i} className="px-3 py-5 md:px-5 md:py-6 text-left md:text-center">
              <p className="font-display text-teal text-h2-m md:text-h2-d leading-none">
                {d.value}
              </p>
              <p className="mt-3 font-sans uppercase text-caption-m md:text-caption-d text-cream/70">
                {d.label}
              </p>
              <p className="mt-2 font-sans text-cream/50 text-body-m md:text-body-d">
                {d.sub}
              </p>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
