// Capability stack — four large feature blocks alternating image/text sides.
// Each is a self-contained "what Solvere does" pillar.

import { FadeIn } from "@/components/FadeIn";

const PILLARS = [
  {
    eyebrow: "END-TO-END RECOVERY",
    title: "We work your denied claims from export to recovered payment.",
    body:
      "Classification, documentation, resubmission, appeals, payer follow-up — handled. You hand us 90 days of denials and step away until cash lands in the clinic's account.",
    accent: "01",
  },
  {
    eyebrow: "AI PLUS LICENSED CODING",
    title: "AI scores recoverability across hundreds of claims in minutes.",
    body:
      "A DHA-licensed medical coder verifies every high-value or complex submission before it goes back to the payer. AI does the volume. A human does the judgement.",
    accent: "02",
  },
  {
    eyebrow: "EVERY UAE PAYER PORTAL",
    title: "Daman, Thiqa, NEXtCARE, NAS, MedNet — and the rest of them.",
    body:
      "We file resubmissions and appeals through eClaimLink and every major UAE payer portal. We learn each payer's denial patterns claim by claim, so the next recovery is faster than the last.",
    accent: "03",
  },
  {
    eyebrow: "PAY ONLY ON RECOVERY",
    title: "Twenty percent of recovered cash. Nothing else.",
    body:
      "No setup fee. No software fee. No retainer. If Solvere recovers nothing, you pay nothing. The only thing you risk is the ten minutes it takes your biller to export the file.",
    accent: "04",
  },
];

export function CapabilityStack() {
  return (
    <section
      aria-label="What Solvere does"
      className="bg-cream-deep py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            WHAT SOLVERE DOES
          </p>
          <h2 className="mt-3 md:mt-4 font-display text-ink text-h2-m md:text-h2-d">
            Four pillars. One outcome: cash in your account.
          </h2>
        </FadeIn>

        <div className="mt-7 md:mt-8 space-y-0 border-t border-rule">
          {PILLARS.map((p, i) => (
            <FadeIn key={p.accent} delay={0.08 * i}>
              <article className="grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6 py-6 md:py-7 border-b border-rule">
                <div className="md:col-span-3">
                  <p className="font-display text-teal text-h1-m md:text-h1-d leading-none tabular-nums">
                    {p.accent}
                  </p>
                  <p className="mt-3 md:mt-4 font-sans uppercase text-caption-m md:text-caption-d text-ink/70 tracking-[0.14em]">
                    {p.eyebrow}
                  </p>
                </div>
                <div className="md:col-span-9">
                  <h3 className="font-display text-ink text-h3-m md:text-h2-d max-w-prose">
                    {p.title}
                  </h3>
                  <p className="mt-3 md:mt-4 font-sans text-muted text-body-m md:text-body-lg-d max-w-prose">
                    {p.body}
                  </p>
                </div>
              </article>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
