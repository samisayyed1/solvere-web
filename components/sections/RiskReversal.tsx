// §7.6 — Risk Reversal. Cream-deep band. Three H2-sized lines, centered, 32px spacing.

import { FadeIn } from "@/components/FadeIn";

const LINES = [
  "No software to install.",
  "No integration with your PMS.",
  "Pay only when you are paid.",
];

export function RiskReversal() {
  return (
    <section
      aria-label="Risk Reversal"
      className="bg-cream-deep py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5 text-center">
        <FadeIn>
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            WHY CLINICS SAY YES
          </p>
        </FadeIn>

        <div className="mt-5 md:mt-6 space-y-4 md:space-y-4">
          {LINES.map((line, i) => (
            <FadeIn key={line} delay={0.08 * (i + 1)}>
              <p className="font-display text-ink text-h2-m md:text-h2-d">
                {line}
              </p>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.4} className="mt-5 md:mt-6">
          <p className="mx-auto max-w-[580px] font-sans text-muted text-body-m md:text-body-d">
            Solvere carries the operational and financial risk. Your downside
            is zero.
          </p>
        </FadeIn>
      </div>
    </section>
  );
}
