"use client";

import { motion } from "framer-motion";

type Payer = { name: string; code: string; tag: "UAE" | "TPA" | "INTL" };

const payers: Payer[] = [
  { name: "Daman", code: "DM", tag: "UAE" },
  { name: "Thiqa", code: "TH", tag: "UAE" },
  { name: "NEXtCARE", code: "NX", tag: "TPA" },
  { name: "NAS", code: "NA", tag: "TPA" },
  { name: "MedNet", code: "MN", tag: "TPA" },
  { name: "ADNIC", code: "AD", tag: "UAE" },
  { name: "Sukoon", code: "SK", tag: "UAE" },
  { name: "Orient", code: "OR", tag: "UAE" },
  { name: "Oman Insurance", code: "OI", tag: "UAE" },
  { name: "AAFAQ", code: "AF", tag: "UAE" },
  { name: "Saico", code: "SA", tag: "UAE" },
  { name: "National Gen.", code: "NG", tag: "UAE" },
  { name: "Bupa Arabia", code: "BU", tag: "INTL" },
  { name: "MetLife", code: "ML", tag: "INTL" },
  { name: "AXA", code: "AX", tag: "INTL" },
  { name: "Cigna", code: "CG", tag: "INTL" },
  { name: "Now Health", code: "NH", tag: "INTL" },
  { name: "Mednet Global", code: "MG", tag: "INTL" },
  { name: "Aetna", code: "AE", tag: "INTL" },
  { name: "Allianz", code: "AL", tag: "INTL" },
  { name: "GIG Gulf", code: "GG", tag: "UAE" },
  { name: "Watania", code: "WT", tag: "UAE" },
  { name: "Salama", code: "SL", tag: "UAE" },
  { name: "RSA", code: "RS", tag: "INTL" },
];

const tickerLine = [
  "Daman", "Thiqa", "NEXtCARE", "NAS", "MedNet", "ADNIC", "Sukoon",
  "Orient", "Bupa", "MetLife", "AXA", "Cigna", "Aetna", "Allianz",
];

export default function PayerMarquee() {
  return (
    <section className="relative bg-cream py-20 md:py-24 border-y border-rule overflow-hidden">
      <div className="mx-auto max-w-container px-6 lg:px-10">
        {/* header row */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-end mb-12">
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

        {/* curated payer grid */}
        <div className="relative rounded-2xl border border-rule bg-cream-deep/60 overflow-hidden">
          {/* legend strip — stacks on mobile so labels don't overlap, single row from sm: up */}
          <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-rule border-b border-rule">
            <LegendCell label="UAE Local" count={14} />
            <LegendCell label="TPA Networks" count={3} />
            <LegendCell label="International" count={7} />
          </div>

          {/* 6 × 4 grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 divide-x divide-y divide-rule">
            {payers.map((p, i) => (
              <PayerCell key={p.name} payer={p} index={i} />
            ))}
          </div>
        </div>

        {/* ticker line */}
        <div className="mt-10 relative">
          <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-r from-cream to-transparent" />
          <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-l from-cream to-transparent" />
          <div className="overflow-hidden">
            <div className="flex gap-10 whitespace-nowrap marquee-track items-center text-[12px] tracking-[0.22em] uppercase text-muted/80">
              {[...tickerLine, ...tickerLine].map((p, i) => (
                <div key={i} className="flex items-center gap-10 shrink-0">
                  <span className="flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-teal" />
                    {p}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-10 flex items-center justify-between flex-wrap gap-4 text-[11px] tracking-[0.22em] uppercase text-muted">
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

function LegendCell({
  label,
  count,
}: {
  label: string;
  count: number;
}) {
  return (
    <div
      className="px-5 py-3.5 flex items-center gap-3 text-[10px] tracking-[0.22em] uppercase text-muted"
    >
      <span className="w-1 h-1 rounded-full bg-teal" />
      <span>{label}</span>
      <span className="text-ink-soft tabular-nums">·</span>
      <span className="text-ink-soft tabular-nums">
        {String(count).padStart(2, "0")}
      </span>
    </div>
  );
}

function PayerCell({ payer, index }: { payer: Payer; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{
        duration: 0.45,
        delay: (index % 6) * 0.04 + Math.floor(index / 6) * 0.05,
        ease: [0.22, 1, 0.36, 1],
      }}
      className="group relative px-5 py-6 md:py-7 bg-cream-deep/40 hover:bg-cream transition-colors min-h-[110px] flex flex-col justify-between"
    >
      <div className="flex items-start justify-between">
        <span className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-ink/[0.04] text-[10px] tracking-wider font-semibold text-ink-soft border border-rule group-hover:border-teal/30 group-hover:text-teal transition-colors">
          {payer.code}
        </span>
        <span className="text-[9px] tracking-[0.22em] uppercase text-muted/70">
          {payer.tag}
        </span>
      </div>
      <div className="mt-4">
        <div className="h-serif text-[18px] md:text-[19px] text-ink leading-[1.1] tracking-[-0.01em]">
          {payer.name}
        </div>
      </div>
    </motion.div>
  );
}
