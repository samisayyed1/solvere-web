"use client";

import { motion } from "framer-motion";

const stats = [
  {
    no: "01",
    value: "60–70%",
    label: "Of denied claims are recoverable on appeal",
    sub: "Industry baseline · UAE",
  },
  {
    no: "02",
    value: "35%",
    label: "What UAE clinics currently recover today",
    sub: "Where the gap lives",
  },
  {
    no: "03",
    value: "5 days",
    label: "From file upload to recoverability audit",
    sub: "First number, on your data",
  },
  {
    no: "04",
    value: "AED 0",
    label: "Upfront. Pay only on what we recover.",
    sub: "20% of recovered cash, nothing else",
  },
];

export default function StatsBand() {
  return (
    <section className="relative bg-ink text-cream py-20 md:py-28 grain overflow-hidden">
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.05] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "120px 100%",
        }}
      />
      <div
        aria-hidden
        className="absolute -top-32 left-1/2 -translate-x-1/2 w-[820px] h-[820px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(14,94,94,0.12), rgba(14,94,94,0) 70%)",
        }}
      />

      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-10 lg:gap-16 items-end mb-16">
          <div>
            <div className="eyebrow mb-5 text-teal">The numbers</div>
            <h2 className="h-display text-[36px] sm:text-[46px] md:text-[60px] text-cream leading-[1.02] max-w-[18ch]">
              The rules of UAE claim recovery,{" "}
              <span className="italic font-normal text-teal">rewritten.</span>
            </h2>
          </div>
          <p className="text-[15px] md:text-[16px] text-cream/55 leading-[1.6] max-w-[42ch] lg:justify-self-end">
            Four numbers that describe the entire opportunity. Every line on
            this site exists to move the third one — and zero the fourth.
          </p>
        </div>

        <div className="border-t border-white/12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
            {stats.map((s, i) => (
              <StatTile key={s.no} stat={s} delay={i * 0.1} isLast={i === stats.length - 1} />
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
  isLast,
}: {
  stat: { no: string; value: string; label: string; sub: string };
  delay: number;
  isLast: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`relative py-10 md:py-12 px-6 lg:px-8 first:pl-0 flex flex-col gap-8 border-b md:border-b-0 md:[&:not(:last-child)]:border-r border-white/12`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] tracking-[0.22em] uppercase text-cream/40 font-medium">
          {stat.no}
        </span>
        <span className="text-[10px] tracking-[0.22em] uppercase text-cream/35">
          {stat.sub}
        </span>
      </div>

      <div className="flex items-baseline">
        <span className="h-display text-[56px] sm:text-[64px] md:text-[72px] lg:text-[76px] text-teal leading-[0.95] whitespace-nowrap tracking-[-0.04em]">
          {stat.value}
        </span>
      </div>

      <p className="text-[14px] md:text-[15px] text-cream/65 leading-[1.5] max-w-[28ch]">
        {stat.label}
      </p>
    </motion.div>
  );
}
