// §7.5 — How It Works. Cream bg. Four steps. Above the 2×2 grid sits a
// teal horizontal "process flow" graphic: 4 circular nodes (numbered) linked
// by a teal hairline, with short labels beneath each. Mobile keeps the
// vertical list of step cards; the process flow renders on desktop only.

import { Fragment } from "react";
import { FadeIn } from "@/components/FadeIn";

const STEPS = [
  {
    n: "01",
    short: "Send",
    title: "Send us your denied claims",
    body:
      "Export the last 90 days of denials from your billing system. One file. Ten minutes of your time.",
  },
  {
    n: "02",
    short: "Analyze",
    title: "We analyze every claim",
    body:
      "Our AI agents and a DHA-licensed medical coder review each denial, classify the reason, and identify what's recoverable. You receive an audit within five working days.",
  },
  {
    n: "03",
    short: "Resubmit",
    title: "We resubmit and appeal",
    body:
      "We handle resubmissions and appeals through eClaimLink and payer portals — Daman, Thiqa, NEXtCARE, NAS, MedNet, and others. Documentation, follow-up, escalation — all done by us.",
  },
  {
    n: "04",
    short: "Paid",
    title: "You pay only when we recover",
    body:
      "Twenty percent of recovered cash. Nothing else. No software fee. No setup fee. If we don't recover, you pay zero.",
  },
];

export function HowItWorks() {
  return (
    <section
      aria-label="How It Works"
      className="bg-cream py-7 md:py-8 border-t border-rule"
    >
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

        {/* Process-flow graphic — desktop only. Four teal-bordered circles
            connected by a single teal hairline that runs through the centers. */}
        <FadeIn delay={0.16} className="mt-7 md:mt-8 hidden md:block">
          <div className="relative mx-auto max-w-3xl">
            {/* Connecting line — positioned at the vertical centre of the
                circles (w-14 h-14 → centre at 28px), runs from inside circle 1
                to inside circle 4. The circle backgrounds cover the line at
                each node so it reads as a connected timeline. */}
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

        {/* Detailed step grid */}
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
