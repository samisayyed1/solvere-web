// §7.4 — The Gap. Cream bg. Three stats with static teal progress bars beneath.
// Editorial 3-column layout: col 1 left, col 2 centered, col 3 right (desktop).
// Implemented with flex-col + items-start/center/end so the stat blocks are
// pushed to their column edges (text-align won't relocate a block child with
// whitespace-nowrap). Mobile stacks single-column, fully centered.

import { FadeIn } from "@/components/FadeIn";

const STATS = [
  {
    value: "35%",
    label: "RECOVERED TODAY",
    caption: "The current UAE clinic average for denied claims",
    fillPct: 35,
    align: "left",
  },
  {
    value: "60–70%",
    label: "ACTUALLY RECOVERABLE",
    caption: "Industry benchmark on appeal-eligible denials",
    fillPct: 65,
    align: "center",
  },
  {
    value: "AED 1.2M+",
    label: "LEFT ON THE TABLE",
    caption: "Estimated annual loss per AED 20M of revenue",
    fillPct: 100,
    align: "right",
  },
] as const;

const ITEMS_AXIS: Record<string, string> = {
  left: "items-center md:items-start",
  center: "items-center",
  right: "items-center md:items-end",
};

const TEXT_AXIS: Record<string, string> = {
  left: "text-center md:text-left",
  center: "text-center",
  right: "text-center md:text-right",
};

export function TheGap() {
  return (
    <section aria-label="The Gap" className="bg-cream py-7 md:py-8 border-t border-rule">
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="text-center">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            THE GAP
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-3 md:mt-4 text-center">
          <h2 className="mx-auto max-w-narrow font-display text-ink text-h2-m md:text-h2-d">
            Most denied claims are recoverable. Most are never recovered.
          </h2>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-3 md:divide-x divide-y md:divide-y-0 divide-rule border-t border-rule">
          {STATS.map((s, i) => (
            <FadeIn key={s.label} delay={0.08 * i} className="px-3 py-5 md:px-5 md:py-6">
              <div className={`flex flex-col ${ITEMS_AXIS[s.align]}`}>
                <p className="font-display text-teal text-[56px] md:text-[72px] leading-none whitespace-nowrap tabular-nums">
                  {s.value}
                </p>

                {/* Static progress bar — aligns with the stat block edge */}
                <div
                  className="mt-4 md:mt-5 h-[3px] w-full max-w-[180px] bg-cream-deep relative"
                  role="presentation"
                  aria-hidden
                >
                  <div
                    className="absolute inset-y-0 left-0 bg-teal"
                    style={{ width: `${s.fillPct}%` }}
                  />
                </div>

                <p className={`mt-4 font-sans uppercase text-caption-m md:text-caption-d text-ink ${TEXT_AXIS[s.align]}`}>
                  {s.label}
                </p>
                <p className={`mt-2 font-sans text-muted text-body-m md:text-body-d max-w-[280px] ${TEXT_AXIS[s.align]}`}>
                  {s.caption}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.24} className="mt-5 md:mt-6 text-center">
          <p className="mx-auto max-w-prose font-sans text-muted text-body-m md:text-body-d">
            Solvere closes the gap with AI agents and UAE-licensed medical
            coders, on a pure pay-on-recovery basis.
          </p>
        </FadeIn>
      </div>
    </section>
  );
}
