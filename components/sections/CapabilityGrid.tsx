// Capability grid — what Solvere actually does. Four cards in a 2×2 grid,
// adapted from the Amperos "End-to-end / First-touch / Complex / Configurable"
// pattern but specific to UAE clinic claim recovery.
//
// Sits between the Hero and The Number so first-time visitors see the
// service shape immediately after the pitch.

import { FadeIn } from "@/components/FadeIn";

const CAPABILITIES = [
  {
    eyebrow: "END-TO-END RECOVERY",
    title: "We work your claims from export to recovered cash",
    body:
      "Classification, documentation, resubmission, appeals, follow-up — all done by us. You hand us the file and step away until the wire lands.",
  },
  {
    eyebrow: "AI + DHA-LICENSED CODING",
    title: "AI scores recoverability. A licensed coder verifies.",
    body:
      "Our agents triage hundreds of denied claims in minutes. A DHA-licensed medical coder reviews every high-value or complex claim before it goes back to the payer.",
  },
  {
    eyebrow: "EVERY UAE PAYER PORTAL",
    title: "Daman, Thiqa, NEXtCARE, NAS, MedNet and the rest",
    body:
      "We file resubmissions and appeals through eClaimLink and the major UAE payer portals. We learn each payer's denial patterns claim by claim.",
  },
  {
    eyebrow: "PAY ONLY ON RECOVERY",
    title: "Twenty percent of recovered cash. Nothing else.",
    body:
      "No setup fee. No software fee. No retainer. If we don't recover, you pay zero. Your downside is bounded at exactly the time it takes to export the file.",
  },
];

export function CapabilityGrid() {
  return (
    <section
      aria-label="What Solvere does"
      className="bg-cream-deep py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="text-center">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            WHAT SOLVERE DOES
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-3 md:mt-4 text-center">
          <h2 className="mx-auto max-w-narrow font-display text-ink text-h2-m md:text-h2-d">
            Built for clinics that can&apos;t afford to write off cash.
          </h2>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-2 gap-0 border-t border-rule">
          {CAPABILITIES.map((c, i) => (
            <FadeIn
              key={c.eyebrow}
              delay={0.08 * i}
              className={[
                "border-b border-rule",
                i % 2 === 0 ? "md:border-r" : "",
              ].join(" ")}
            >
              <div className="px-3 py-5 md:px-6 md:py-7">
                <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
                  {c.eyebrow}
                </p>
                <h3 className="mt-3 font-display text-ink text-h3-m md:text-h3-d max-w-prose">
                  {c.title}
                </h3>
                <p className="mt-3 font-sans text-muted text-body-m md:text-body-d max-w-prose">
                  {c.body}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
