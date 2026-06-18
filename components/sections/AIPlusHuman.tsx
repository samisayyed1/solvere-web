// AI + Human team section — Solvere's "AI-native, human-verified" differentiator.
// Modeled on Amperos's "AI-native collections backed by RCM experts" pattern
// (4 dimensions arranged as a single rich block). Adapted for UAE-specific
// reality: AI scoring + DHA-licensed coder verification + every payer's portal +
// data flywheel.

import { FadeIn } from "@/components/FadeIn";

const DIMENSIONS = [
  {
    n: "01",
    title: "AI reads every denial",
    body:
      "Classification, reason coding, recoverability scoring across hundreds of claims at once. The triage that used to take a biller a week happens in minutes.",
  },
  {
    n: "02",
    title: "A licensed coder verifies",
    body:
      "Every high-value or complex claim is reviewed by a DHA-licensed medical coder before it goes back to the payer. The human gate before the payer gateway.",
  },
  {
    n: "03",
    title: "Every payer's portal",
    body:
      "Resubmission and appeal through eClaimLink, Daman, Thiqa, NEXtCARE, NAS, MedNet, ADNIC, Sukoon, and the rest. Documentation, follow-up, escalation — handled end-to-end.",
  },
  {
    n: "04",
    title: "Every recovery trains the next",
    body:
      "The system learns from each payer response. After ten thousand claims, our denial-reason library is the moat that nobody else in the GCC can rebuild quickly.",
  },
];

export function AIPlusHuman() {
  return (
    <section
      aria-label="AI plus human verification"
      className="bg-cream py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="text-center">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            WHY THIS WORKS
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-3 md:mt-4 text-center">
          <h2 className="mx-auto max-w-narrow font-display text-ink text-h2-m md:text-h2-d">
            AI-native recovery, human-verified.
          </h2>
        </FadeIn>

        <FadeIn delay={0.16} className="mt-3 md:mt-4 text-center">
          <p className="mx-auto max-w-prose font-sans text-muted text-body-m md:text-body-d">
            Pure-AI vendors miss what the rules don&apos;t cover. Pure-human shops can&apos;t scale.
            Solvere ships both, in the same loop.
          </p>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-2 gap-x-6 md:gap-x-8 gap-y-6 md:gap-y-7">
          {DIMENSIONS.map((d, i) => (
            <FadeIn key={d.n} delay={0.08 * i}>
              <div className="border-t border-rule pt-4 md:pt-5">
                <p className="font-display text-teal text-h2-m md:text-h2-d leading-none tabular-nums">
                  {d.n}
                </p>
                <h3 className="mt-3 font-display text-ink text-h3-m md:text-h3-d">
                  {d.title}
                </h3>
                <p className="mt-2 font-sans text-muted text-body-m md:text-body-d max-w-prose">
                  {d.body}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
