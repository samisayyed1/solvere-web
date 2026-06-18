// Process flow — four steps from claim export to recovered payment.
// Numbered timeline with connecting line on desktop, vertical on mobile.

import { FadeIn } from "@/components/FadeIn";

const STEPS = [
  {
    n: "01",
    short: "Export",
    title: "Send us 90 days of denied claims",
    body:
      "Your biller pulls the file from your billing system. One export, ten minutes of their time. We sign an NDA before the file moves.",
  },
  {
    n: "02",
    short: "Audit",
    title: "We return a recoverability audit in five days",
    body:
      "Our AI agents classify every denial and score recoverability. A DHA-licensed coder verifies. You see the specific AED number we can recover from your data before you commit anything.",
  },
  {
    n: "03",
    short: "Work",
    title: "We resubmit and appeal every workable claim",
    body:
      "End-to-end through eClaimLink and every UAE payer portal. Documentation, follow-up, escalation — all done by us. You get a monthly recovery report per payer.",
  },
  {
    n: "04",
    short: "Paid",
    title: "You pay twenty percent of what lands",
    body:
      "And nothing else. No software fee, no setup fee, no retainer. If we recover zero, you owe zero. Cancel anytime, no termination fee.",
  },
];

export function ProcessFlow() {
  return (
    <section
      id="how-it-works"
      aria-label="How it works"
      className="bg-cream py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            HOW IT WORKS
          </p>
          <h2 className="mt-3 md:mt-4 font-display text-ink text-h2-m md:text-h2-d">
            Four steps. Five days to first audit. Zero risk.
          </h2>
        </FadeIn>

        {/* Process indicator — desktop only */}
        <FadeIn delay={0.08} className="mt-7 md:mt-8 hidden md:block">
          <div className="relative mx-auto max-w-3xl">
            <div
              aria-hidden
              className="absolute top-[28px] left-[7%] right-[7%] h-px bg-teal/40"
            />
            <div className="relative flex justify-between">
              {STEPS.map((s) => (
                <div key={s.n} className="flex flex-col items-center w-[120px]">
                  <div className="w-14 h-14 rounded-full bg-cream border-2 border-teal flex items-center justify-center font-display font-medium text-teal text-[18px] tabular-nums">
                    {s.n}
                  </div>
                  <p className="mt-3 font-sans uppercase tracking-[0.14em] text-teal text-[11px] font-medium">
                    {s.short}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-7">
          {STEPS.map((s, i) => (
            <FadeIn key={s.n} delay={0.08 * i}>
              <article className="border-t border-rule pt-4 md:pt-5">
                <p className="font-display text-teal text-h1-m md:text-h1-d leading-none tabular-nums">
                  {s.n}
                </p>
                <h3 className="mt-3 font-display text-ink text-h3-m md:text-h3-d max-w-prose">
                  {s.title}
                </h3>
                <p className="mt-2 max-w-prose font-sans text-muted text-body-m md:text-body-d">
                  {s.body}
                </p>
              </article>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
