"use client";

const localPayers = [
  "Daman", "Thiqa", "NEXtCARE", "NAS", "MedNet", "ADNIC", "Sukoon",
  "Orient", "Oman Insurance", "AAFAQ", "Saico", "National General",
];
const internationalPayers = [
  "Bupa Arabia", "MetLife", "AXA", "Cigna", "Now Health", "Mednet Global",
  "Aetna", "Allianz", "GIG Gulf", "Watania", "Salama", "RSA",
];

export default function PayerMarquee() {
  return (
    <section className="relative bg-cream py-20 md:py-24 border-y border-rule overflow-hidden">
      <div className="mx-auto max-w-container px-6 lg:px-10 mb-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-7">
            <div className="eyebrow mb-5">Payers we work</div>
            <h2 className="h-serif text-[30px] sm:text-[38px] md:text-[46px] text-ink leading-[1.05] max-w-[22ch]">
              Every UAE payer portal.{" "}
              <span className="italic text-teal">Every escalation path.</span>
            </h2>
          </div>
          <div className="lg:col-span-5 lg:justify-self-end flex items-center gap-8 lg:gap-10">
            <Metric value="24+" label="Payer portals" />
            <Hairline />
            <Metric value="100%" label="UAE coverage" />
            <Hairline />
            <Metric value="GCC" label="Roadmap" />
          </div>
        </div>
      </div>

      <div className="relative">
        <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-32 z-10 bg-gradient-to-r from-cream to-transparent" />
        <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-32 z-10 bg-gradient-to-l from-cream to-transparent" />

        <MarqueeRow
          label="UAE LOCAL PAYERS"
          items={localPayers}
          reverse={false}
        />
        <div className="my-3 mx-auto max-w-container px-6 lg:px-10">
          <div className="h-px bg-rule" />
        </div>
        <MarqueeRow
          label="INTERNATIONAL · TPA"
          items={internationalPayers}
          reverse={true}
        />
      </div>

      <div className="mx-auto max-w-container px-6 lg:px-10 mt-12">
        <div className="flex items-center justify-between flex-wrap gap-4 text-[11px] tracking-[0.22em] uppercase text-muted">
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-teal" />
            Filed via eClaimLink + direct portals
          </span>
          <span>Updated quarterly</span>
        </div>
      </div>
    </section>
  );
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex flex-col">
      <span className="h-display text-[26px] md:text-[30px] text-ink leading-none tabular-nums tracking-tight">
        {value}
      </span>
      <span className="mt-2 text-[10px] tracking-[0.22em] uppercase text-muted">
        {label}
      </span>
    </div>
  );
}

function Hairline() {
  return <span aria-hidden className="w-px h-10 bg-rule" />;
}

function MarqueeRow({
  label,
  items,
  reverse,
}: {
  label: string;
  items: string[];
  reverse: boolean;
}) {
  const seq = [...items, ...items];
  return (
    <div className="relative py-3 flex items-center">
      <div className="absolute left-0 lg:left-10 top-1/2 -translate-y-1/2 z-20 hidden md:flex items-center gap-2 text-[10px] tracking-[0.22em] uppercase text-muted bg-cream pr-4">
        <span className="w-1 h-1 rounded-full bg-teal" />
        {label}
      </div>
      <div className="overflow-hidden w-full md:pl-[210px]">
        <div
          className={`flex gap-10 md:gap-14 whitespace-nowrap marquee-track`}
          style={{
            animationDirection: reverse ? "reverse" : "normal",
            animationDuration: reverse ? "70s" : "55s",
          }}
        >
          {seq.map((p, i) => (
            <div
              key={`${p}-${i}`}
              className="flex items-center gap-10 md:gap-14"
            >
              <span className="h-serif text-[24px] md:text-[30px] text-ink/85 hover:text-teal transition-colors tracking-[-0.01em]">
                {p}
              </span>
              <span aria-hidden className="text-rule">
                <svg width="6" height="6" viewBox="0 0 6 6">
                  <circle cx="3" cy="3" r="2" fill="currentColor" />
                </svg>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
