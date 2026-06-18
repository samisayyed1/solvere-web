"use client";

import { motion } from "framer-motion";

const stats = [
  {
    no: "01",
    value: "60–70%",
    label: "Of denied claims are recoverable on appeal.",
  },
  {
    no: "02",
    value: "35%",
    label: "What UAE clinics currently recover today.",
  },
  {
    no: "03",
    value: "5 days",
    label: "From file upload to recoverability audit.",
  },
  {
    no: "04",
    value: "AED 0",
    label: "Upfront. Pay only on what we recover.",
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

      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-end mb-16 md:mb-20">
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

        <div className="border-t border-white/12 grid grid-cols-2 lg:grid-cols-4">
          {stats.map((s, i) => (
            <StatTile
              key={s.no}
              stat={s}
              delay={i * 0.1}
              isLastInRow={(i + 1) % 4 === 0}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function StatTile({
  stat,
  delay,
}: {
  stat: { no: string; value: string; label: string };
  delay: number;
  isLastInRow?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className="relative min-w-0 flex flex-col px-6 lg:px-7 pt-6 pb-10 lg:pt-7 lg:pb-12 gap-8 lg:gap-10 min-h-[280px] border-r border-b lg:border-b-0 last:border-r-0 [&:nth-child(2)]:border-r-0 lg:[&:nth-child(2)]:border-r border-white/12"
    >
      {/* index header */}
      <div className="flex items-center justify-between text-[11px] tracking-[0.22em] uppercase text-cream/40 font-medium">
        <span>{stat.no}</span>
        <span className="text-cream/25">/ 04</span>
      </div>

      {/* value — fluid clamp so it never overflows */}
      <div className="flex-1 flex items-end min-w-0">
        <span
          className="h-display text-teal leading-[0.9] whitespace-nowrap tracking-[-0.04em] block min-w-0"
          style={{
            fontSize: "clamp(38px, 5vw, 64px)",
          }}
        >
          {stat.value}
        </span>
      </div>

      {/* label */}
      <p className="text-[14px] md:text-[15px] text-cream/65 leading-[1.5] max-w-[26ch]">
        {stat.label}
      </p>
    </motion.div>
  );
}
