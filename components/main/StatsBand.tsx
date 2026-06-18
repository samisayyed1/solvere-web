// Big stats band — four headline numbers in a horizontal row on ink.
// Numbers are static (no counter animation — banned in DESIGN.md §14).
// Values sourced from Solvere master plan + Hormozi value-equation playbook.

import { FadeIn } from "@/components/FadeIn";

const STATS = [
  { v: "60–70%", l: "Of denied claims are recoverable on appeal" },
  { v: "35%", l: "What UAE clinics currently recover today" },
  { v: "5 days", l: "From file upload to recoverability audit" },
  { v: "0", l: "AED upfront. Pay only on what we recover." },
];

export function StatsBand() {
  return (
    <section
      aria-label="The numbers"
      className="bg-ink py-7 md:py-8 border-t border-cream/10"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            THE NUMBERS
          </p>
          <h2 className="mt-3 md:mt-4 font-display text-cream text-h2-m md:text-h2-d">
            The rules of UAE claim recovery, rewritten.
          </h2>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-2 md:grid-cols-4 gap-y-7 border-t border-cream/10 pt-6 md:pt-7">
          {STATS.map((s, i) => (
            <FadeIn key={s.l} delay={0.08 * i}>
              <div className="px-2 md:px-4">
                <p className="font-display text-teal text-[44px] md:text-[64px] leading-none tabular-nums whitespace-nowrap">
                  {s.v}
                </p>
                <p className="mt-4 font-sans text-cream/70 text-body-m md:text-body-d max-w-[220px]">
                  {s.l}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
