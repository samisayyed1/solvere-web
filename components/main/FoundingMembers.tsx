// Founding-member offer band — first 10 clinics get locked-rate access.
// Per Solvere Grand Slam Offer Playbook §6 (Post-Yes Execution Sequence)
// and the WhatsApp "founding members get a locked rate for life" line.

import { FadeIn } from "@/components/FadeIn";
import { BookACallButton } from "@/components/BookACallButton";

const TERMS = [
  "Lifetime locked rate — never reprices",
  "Direct founder access on WhatsApp",
  "First-look at every new payer integration",
  "Priority on the recovery queue",
];

export function FoundingMembers() {
  return (
    <section
      aria-label="Founding member program"
      className="bg-cream-deep py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <div className="md:grid md:grid-cols-12 md:gap-7 md:items-start">
          <div className="md:col-span-5">
            <FadeIn>
              <p className="font-sans uppercase text-caption-m md:text-caption-d text-amber">
                FOUNDING MEMBERS
              </p>
              <h2 className="mt-3 md:mt-4 font-display text-ink text-h2-m md:text-h2-d">
                Ten clinics. Locked-in pricing for the lifetime of the contract.
              </h2>
            </FadeIn>
          </div>

          <div className="md:col-span-7 mt-5 md:mt-0">
            <FadeIn delay={0.08}>
              <p className="font-sans text-muted text-body-m md:text-body-lg-d max-w-prose">
                We&apos;re selecting ten UAE clinics as Solvere&apos;s founding cohort.
                The rate you sign at on day one stays at that rate forever.
                We&apos;ll take what we learn from your data and use it to build
                the rest of the recovery system in the open with you.
              </p>
            </FadeIn>

            <FadeIn delay={0.16}>
              <ul className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-x-5 gap-y-3 border-t border-rule pt-5">
                {TERMS.map((t) => (
                  <li
                    key={t}
                    className="flex items-start gap-3 font-sans text-ink text-body-m md:text-body-d"
                  >
                    <span
                      aria-hidden
                      className="mt-[6px] inline-block h-[6px] w-[6px] rounded-full bg-teal shrink-0"
                    />
                    {t}
                  </li>
                ))}
              </ul>
            </FadeIn>

            <FadeIn delay={0.24}>
              <div className="mt-7 flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
                <BookACallButton label="Apply to the founding cohort" />
                <p className="font-sans text-muted text-caption-m md:text-caption-d uppercase tracking-[0.14em]">
                  Spots remaining: limited
                </p>
              </div>
            </FadeIn>
          </div>
        </div>
      </div>
    </section>
  );
}
