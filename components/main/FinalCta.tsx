// Final CTA — strong close on ink. Single decision: book the audit call.

import { FadeIn } from "@/components/FadeIn";
import { BookACallButton } from "@/components/BookACallButton";

export function FinalCta() {
  return (
    <section
      aria-label="Final call to action"
      className="bg-ink py-7 md:py-8 border-t border-cream/10"
    >
      <div className="mx-auto max-w-content px-3 md:px-5 text-center">
        <FadeIn>
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            START THE RECOVERY
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-3 md:mt-4">
          <h2 className="mx-auto max-w-narrow font-display text-cream text-h1-m md:text-h1-d">
            Ready to recover what your clinic is owed?
          </h2>
        </FadeIn>

        <FadeIn delay={0.16} className="mt-4 md:mt-5">
          <p className="mx-auto max-w-prose font-sans text-cream/70 text-body-m md:text-body-lg-d">
            Send us your last ninety days of denials. We&apos;ll return a
            recoverability audit in five working days. No software. No upfront
            fee. No risk.
          </p>
        </FadeIn>

        <FadeIn delay={0.24} className="mt-7 flex justify-center">
          <BookACallButton label="Book a 20-minute audit call" />
        </FadeIn>

        <FadeIn delay={0.32} className="mt-4">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-cream/55 tracking-[0.14em]">
            5-DAY AUDIT · PAY ONLY ON RECOVERY · ZERO RISK
          </p>
        </FadeIn>
      </div>
    </section>
  );
}
