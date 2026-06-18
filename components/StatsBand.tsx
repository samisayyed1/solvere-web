"use client";

import { motion } from "framer-motion";

const stats = [
  {
    no: "01",
    value: "60–70%",
    label: "Of denied claims are recoverable on appeal.",
    tag: "Industry baseline",
  },
  {
    no: "02",
    value: "35%",
    label: "What UAE clinics currently recover today.",
    tag: "Today's reality",
  },
  {
    no: "03",
    value: "24 hrs",
    label: "From file upload to recoverability audit.",
    tag: "First number",
  },
  {
    no: "04",
    value: "AED 0",
    label: "Upfront. Pay only on what we recover.",
    tag: "Risk reversal",
  },
];

export default function StatsBand() {
  return (
    <section className="relative bg-ink text-cream py-20 md:py-28 grain overflow-hidden">
      <div
        aria-hidden
        className="absolute -top-32 left-1/2 -translate-x-1/2 w-[860px] h-[860px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(14,94,94,0.14), rgba(14,94,94,0) 70%)",
        }}
      />
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "120px 100%",
        }}
      />

      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-end mb-14 md:mb-16">
          <div className="lg:col-span-7">
            <div className="eyebrow mb-5 text-teal">The numbers</div>
            <h2 className="h-display text-[36px] sm:text-[46px] md:text-[58px] text-cream leading-[1.02] max-w-[18ch]">
              The rules of UAE claim recovery,{" "}
              <span className="italic font-normal text-teal">rewritten.</span>
            </h2>
          </div>
          <p className="lg:col-span-5 text-[15px] md:text-[16px] text-cream/55 leading-[1.6] max-w-[44ch] lg:justify-self-end">
            Four numbers that describe the entire opportunity. Every line on
            this site exists to move the third one — and zero the fourth.
          </p>
        </div>

        {/* premium tile group with consistent rhythm */}
        <div className="rounded-2xl border border-white/12 overflow-hidden">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-x divide-y sm:divide-y-0 lg:divide-y-0 divide-white/10 [&>*:nth-child(2)]:sm:border-l-0 [&>*:nth-child(3)]:lg:border-l-0">
            {stats.map((s, i) => (
              <StatTile key={s.no} stat={s} delay={i * 0.1} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function StatTile({
  stat,
  delay,
}: {
  stat: { no: string; value: string; label: string; tag: string };
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className="relative min-w-0 flex flex-col px-6 lg:px-8 py-9 lg:py-10 gap-5 bg-ink hover:bg-white/[0.015] transition-colors"
    >
      {/* top: index + tag */}
      <div className="flex items-center justify-between text-[10px] tracking-[0.22em] uppercase font-medium">
        <div className="flex items-center gap-2.5 text-cream/45">
          <span className="text-teal">{stat.no}</span>
          <span className="w-3 h-px bg-cream/20" />
          <span>{stat.tag}</span>
        </div>
        <span className="text-cream/25 tabular-nums">/ 04</span>
      </div>

      {/* value — tight to index, fluid clamp */}
      <div className="min-w-0 overflow-hidden">
        <span
          className="h-display text-teal leading-[0.92] whitespace-nowrap tracking-[-0.04em] block min-w-0"
          style={{
            fontSize: "clamp(40px, 3.6vw, 56px)",
          }}
        >
          {stat.value}
        </span>
      </div>

      {/* thin teal accent rule */}
      <div className="w-8 h-px bg-teal/40" />

      {/* label — tight under value */}
      <p className="text-[14px] md:text-[15px] text-cream/70 leading-[1.5] max-w-[28ch]">
        {stat.label}
      </p>
    </motion.div>
  );
}
