// Benefits / outcomes list — five things that change for the clinic
// when Solvere takes over the denied-claim work.

import { FadeIn } from "@/components/FadeIn";

const BENEFITS = [
  {
    title: "Recover the cash your billers gave up on",
    body:
      "The 25–35% your team didn't have time to chase. Recovered into your account on Solvere's bandwidth, not yours.",
  },
  {
    title: "Free your billing team for the work that's already clean",
    body:
      "Let your biller focus on submissions that go through first time. We handle the denials, the appeals, the payer escalation calls.",
  },
  {
    title: "Trade write-offs for recovered revenue",
    body:
      "AED 800K to AED 1.4M per year, on average, for a clinic doing AED 20M revenue. Specific to your data after the five-day audit.",
  },
  {
    title: "Maintain full visibility on every claim",
    body:
      "Claim-by-claim status, recovery rate, payer breakdown. Monthly recovery report delivered to the finance manager — no logins required.",
  },
  {
    title: "Keep the workflow you already have",
    body:
      "No PMS integration. No software to install. No new tab for your team to learn. Your biller exports a file. That's the entire ask.",
  },
];

export function BenefitsList() {
  return (
    <section
      aria-label="What changes for the clinic"
      className="bg-cream-deep py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            WHAT CHANGES
          </p>
          <h2 className="mt-3 md:mt-4 font-display text-ink text-h2-m md:text-h2-d">
            What you get back when Solvere takes the denials.
          </h2>
        </FadeIn>

        <div className="mt-7 md:mt-8 border-t border-rule">
          {BENEFITS.map((b, i) => (
            <FadeIn key={b.title} delay={0.06 * i}>
              <article className="grid grid-cols-1 md:grid-cols-12 gap-3 md:gap-6 py-5 md:py-6 border-b border-rule">
                <div className="md:col-span-1">
                  <p className="font-display text-teal text-h3-m md:text-h3-d leading-none tabular-nums">
                    0{i + 1}
                  </p>
                </div>
                <div className="md:col-span-5">
                  <h3 className="font-display text-ink text-h3-m md:text-h3-d max-w-prose">
                    {b.title}
                  </h3>
                </div>
                <div className="md:col-span-6">
                  <p className="font-sans text-muted text-body-m md:text-body-d max-w-prose">
                    {b.body}
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
