// Payer marquee — between The Number and The Gap. Names only (no logos).
// Ambient horizontal scroll, 60s loop, edge-faded, pauses on hover.
// Distinguished from "trusted by" logo bars (§14 forbidden) — these are payers
// we operate against, not customers we've sold to.

const PAYERS = [
  "Daman",
  "Thiqa",
  "NEXtCARE",
  "NAS",
  "MedNet",
  "ADNIC",
  "Sukoon",
  "Orient",
  "Oman Insurance",
  "Bupa Arabia",
  "MetLife",
  "AXA",
  "Cigna",
  "Now Health",
  "Mednet Global",
  "AAFAQ",
  "Saico",
  "National General",
] as const;

function Track() {
  return (
    <ul className="flex shrink-0 items-center gap-6 md:gap-8 pr-6 md:pr-8">
      {PAYERS.map((name, i) => (
        <li
          key={`${name}-${i}`}
          className="flex items-center gap-6 md:gap-8 whitespace-nowrap"
        >
          <span className="font-display font-medium text-muted text-[32px] md:text-[44px] leading-none">
            {name}
          </span>
          <span
            aria-hidden
            className="block h-6 md:h-8 w-px bg-teal/30"
          />
        </li>
      ))}
    </ul>
  );
}

export function PayerMarquee() {
  return (
    <section
      aria-label="Payers we work"
      className="bg-cream py-7 md:py-8 border-t border-rule overflow-hidden"
    >
      <p className="text-center font-sans uppercase text-caption-m md:text-caption-d text-teal">
        PAYERS WE WORK
      </p>

      <div className="relative mt-5 md:mt-6">
        {/* Edge fades — cream gradient masking */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-cream to-transparent"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-cream to-transparent"
        />

        <div className="solvere-marquee flex w-max">
          <Track />
          <Track />
        </div>
      </div>
    </section>
  );
}
