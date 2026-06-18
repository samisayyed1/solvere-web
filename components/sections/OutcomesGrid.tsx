// Outcomes grid — what changes for the clinic. Mirrors Amperos's "Recover
// more / Reduce AR / Lower cost / Visibility / Time back" pattern but with
// UAE-specific numbers from the Solvere offer playbook.
//
// Sits between How It Works (which explained the process) and Risk Reversal
// (which explains the guarantee). This bridges them by stating outcomes.

import { FadeIn } from "@/components/FadeIn";

const OUTCOMES = [
  {
    value: "AED 800K — 1.4M",
    label: "Recovered per year, on average, for a clinic doing AED 20M revenue.",
  },
  {
    value: "Your billers' time back",
    label: "Your team focuses on what comes through clean. We work the rest.",
  },
  {
    value: "Visibility on every claim",
    label: "Claim-by-claim status, recovery rate, payer breakdown — delivered monthly.",
  },
  {
    value: "Zero new software",
    label: "No PMS integration. No platform to learn. Your team keeps the workflow they have.",
  },
];

export function OutcomesGrid() {
  return (
    <section
      aria-label="What changes for your clinic"
      className="bg-ink py-7 md:py-8 border-t border-cream/10"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="text-center">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            WHAT CHANGES
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-3 md:mt-4 text-center">
          <h2 className="mx-auto max-w-narrow font-display text-cream text-h2-m md:text-h2-d">
            What your clinic gets back.
          </h2>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-2 gap-0 border-t border-cream/10">
          {OUTCOMES.map((o, i) => (
            <FadeIn
              key={o.value}
              delay={0.08 * i}
              className={[
                "border-b border-cream/10",
                i % 2 === 0 ? "md:border-r md:border-cream/10" : "",
              ].join(" ")}
            >
              <div className="px-3 py-5 md:px-6 md:py-7">
                <p className="font-display text-teal text-h3-m md:text-h2-d leading-[1.1]">
                  {o.value}
                </p>
                <p className="mt-3 font-sans text-cream/75 text-body-m md:text-body-d max-w-prose">
                  {o.label}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.32} className="mt-7 md:mt-8 text-center">
          <p className="mx-auto max-w-prose font-sans text-cream/60 text-body-m md:text-body-d">
            Outcomes scale with claim volume. The audit shows your specific recoverable number before you commit.
          </p>
        </FadeIn>
      </div>
    </section>
  );
}
