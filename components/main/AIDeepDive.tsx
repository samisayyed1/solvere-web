// Deep-dive feature section — the Solvere differentiator. Four numbered
// dimensions on ink, each a self-contained pitch for why AI + licensed
// coding wins where pure-AI vendors and pure-human shops both fail.

import { FadeIn } from "@/components/FadeIn";

const DIMENSIONS = [
  {
    eyebrow: "TRIAGE",
    title: "AI reads every denial",
    body:
      "Classification, reason coding, recoverability scoring across hundreds of claims at once. The work that used to take a biller a week happens in minutes — without missing anything that pays.",
  },
  {
    eyebrow: "VERIFICATION",
    title: "A DHA-licensed coder approves",
    body:
      "Every high-value or complex claim is reviewed by a UAE-licensed medical coder before resubmission. The human gate before the payer gateway. Nothing leaves the building unchecked.",
  },
  {
    eyebrow: "EXECUTION",
    title: "End-to-end through every payer's portal",
    body:
      "Resubmission and appeal through eClaimLink, Daman, Thiqa, NEXtCARE, NAS, MedNet, ADNIC, Sukoon and the rest. Documentation, follow-up, escalation — handled to outcome, not just to send.",
  },
  {
    eyebrow: "LEARNING",
    title: "Every recovery trains the next",
    body:
      "Each payer response updates the rule library. After ten thousand claims, our denial-reason knowledge becomes the moat: nobody else in the GCC can rebuild it quickly.",
  },
];

export function AIDeepDive() {
  return (
    <section
      aria-label="How recovery works under the hood"
      className="bg-ink py-7 md:py-8 border-t border-cream/10"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            UNDER THE HOOD
          </p>
          <h2 className="mt-3 md:mt-4 font-display text-cream text-h2-m md:text-h2-d">
            AI-native recovery, human-verified.
          </h2>
          <p className="mt-4 md:mt-5 font-sans text-cream/70 text-body-m md:text-body-lg-d max-w-prose">
            Pure-AI vendors miss what the rules don&apos;t cover. Pure-human
            shops can&apos;t scale. Solvere ships both, in the same loop.
          </p>
        </FadeIn>

        <div className="mt-7 md:mt-8 grid grid-cols-1 md:grid-cols-2 gap-x-6 md:gap-x-8 gap-y-6 md:gap-y-7 border-t border-cream/10 pt-6 md:pt-7">
          {DIMENSIONS.map((d, i) => (
            <FadeIn key={d.title} delay={0.08 * i}>
              <article>
                <p className="font-sans uppercase tracking-[0.16em] text-teal text-caption-m md:text-caption-d">
                  {d.eyebrow}
                </p>
                <h3 className="mt-3 font-display text-cream text-h3-m md:text-h2-d max-w-prose">
                  {d.title}
                </h3>
                <p className="mt-3 font-sans text-cream/70 text-body-m md:text-body-d max-w-prose">
                  {d.body}
                </p>
              </article>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
