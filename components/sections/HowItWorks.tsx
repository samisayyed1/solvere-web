// §7.5 — How It Works. Cream bg. Four steps. Vertical on mobile, 2x2 grid on desktop.
// The numbers are the visual. No icons. No illustrations.

import { FadeIn } from "@/components/FadeIn";

const STEPS = [
  {
    n: "01",
    title: "Send us your denied claims",
    body:
      "Export the last 90 days of denials from your billing system. One file. Ten minutes of your time.",
  },
  {
    n: "02",
    title: "We analyze every claim",
    body:
      "Our AI agents and a DHA-licensed medical coder review each denial, classify the reason, and identify what's recoverable. You receive an audit within five working days.",
  },
  {
    n: "03",
    title: "We resubmit and appeal",
    body:
      "We handle resubmissions and appeals through eClaimLink and payer portals — Daman, Thiqa, NEXtCARE, NAS, MedNet, and others. Documentation, follow-up, escalation — all done by us.",
  },
  {
    n: "04",
    title: "You pay only when we recover",
    body:
      "Twenty percent of recovered cash. Nothing else. No software fee. No setup fee. If we don't recover, you pay zero.",
  },
];

export function HowItWorks() {
  return (
    <section aria-label="How It Works" className="bg-cream py-6 md:py-7">
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="text-center">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            HOW IT WORKS
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-3 md:mt-4 text-center">
          <h2 className="mx-auto max-w-narrow font-display text-ink text-h2-m md:text-h2-d">
            Four steps. Five days to first audit. Zero risk.
          </h2>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-7">
          {STEPS.map((s, i) => (
            <FadeIn key={s.n} delay={0.08 * i}>
              <div className="border-t border-rule pt-4 md:pt-5">
                <p className="font-display text-teal text-h1-m md:text-h1-d leading-none">
                  {s.n}
                </p>
                <h3 className="mt-3 font-display text-ink text-h3-m md:text-h3-d">
                  {s.title}
                </h3>
                <p className="mt-2 max-w-prose font-sans text-muted text-body-m md:text-body-d">
                  {s.body}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
