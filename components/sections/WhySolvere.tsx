// §7.7 — Why Solvere. Ink bg. 2-column desktop (headline left / body right).
// Single-column mobile. Atmospheric photo layer (12% opacity Abu Dhabi dawn)
// adds warmth under the ink — "felt, not seen." Section degrades gracefully
// without the file present.

import { FadeIn } from "@/components/FadeIn";

// TODO: drop a 2048x1280 16:10 Abu Dhabi dawn editorial photo at
//       /public/abu-dhabi-dawn.jpg. The bg-image below references it.
//       Until the file lands, the section renders as pure ink — still on-brief.
//       Generate it via Nano Banana 2 with the prompt:
//
//       "Editorial photograph, 2048x1280, 16:10 cinematic crop. Abu Dhabi
//       corniche at dawn, low golden light, distant skyline of modest
//       medical-district mid-rises (not landmark towers, not Sheikh Zayed
//       Mosque). Heavy negative space in the sky. Wall Street Journal weekday
//       business photo. Muted palette, warm cream/tan sky, low-saturation
//       buildings, no people, no cars, no logos. Subtle film grain. No HDR."

export function WhySolvere() {
  return (
    <section
      aria-label="Why Solvere"
      className="relative bg-ink py-7 md:py-8 border-t border-cream/10 overflow-hidden"
    >
      <div
        aria-hidden
        className="absolute inset-0 bg-cover bg-[center_top] opacity-[0.12] pointer-events-none"
        style={{ backgroundImage: "url(/abu-dhabi-dawn.jpg)" }}
      />

      <div className="relative mx-auto max-w-content px-3 md:px-5">
        <FadeIn>
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-cream/60">
            WHY SOLVERE
          </p>
        </FadeIn>

        <div className="mt-5 md:mt-6 grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-7">
          <FadeIn delay={0.08}>
            <h2 className="font-display text-cream text-h1-m md:text-h1-d">
              Built in the UAE, for the UAE.
            </h2>
          </FadeIn>

          <FadeIn delay={0.16} className="space-y-3 md:space-y-4">
            <p className="font-sans text-cream/80 text-body-lg-m md:text-body-lg-d">
              Solvere is not a US tool retrofitted for the Gulf. We are built
              in Abu Dhabi by people who understand the difference between a
              Daman denial and a Thiqa rejection, between DHA and DoH coding
              rules, between a clinic in Karama and a hospital in Khalifa
              City.
            </p>
            <p className="font-sans text-cream/80 text-body-lg-m md:text-body-lg-d">
              Our agents read every payer&apos;s portal. Our coders are
              licensed by the same authorities your clinic is. Every recovered
              dirham trains the system to recover the next one faster.
            </p>
            <p className="font-sans text-cream/80 text-body-lg-m md:text-body-lg-d">
              When global players enter the region, they will start at zero.
              We will already be the default.
            </p>
          </FadeIn>
        </div>
      </div>
    </section>
  );
}
