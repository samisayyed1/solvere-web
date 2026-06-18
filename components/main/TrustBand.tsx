// Thin trust strip directly under the hero. Single line of credibility
// signals on a cream-deep band — operator, jurisdiction, compliance.

import { FadeIn } from "@/components/FadeIn";

const SIGNALS = [
  "1WEB FZE · Abu Dhabi",
  "DHA-licensed coding",
  "DIFC Data Protection compliant",
  "eClaimLink + payer portals",
];

export function TrustBand() {
  return (
    <section
      aria-label="Operating credentials"
      className="bg-cream-deep border-y border-rule py-4 md:py-5"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn>
          <ul className="flex flex-wrap items-center justify-center gap-x-5 md:gap-x-7 gap-y-2">
            {SIGNALS.map((s) => (
              <li
                key={s}
                className="font-sans uppercase text-caption-m md:text-caption-d text-ink/70 tracking-[0.14em]"
              >
                {s}
              </li>
            ))}
          </ul>
        </FadeIn>
      </div>
    </section>
  );
}
