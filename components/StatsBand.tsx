"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const stats = [
  { value: "60–70%", label: "Of denied claims are recoverable on appeal" },
  { value: "35%", label: "What UAE clinics currently recover today" },
  { value: "5 days", label: "From file upload to recoverability audit" },
  { value: "0", label: "AED upfront. Pay only on what we recover." },
];

export default function StatsBand() {
  return (
    <section className="relative bg-ink text-cream py-20 md:py-28 grain overflow-hidden">
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.06] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.6) 1px, transparent 1px)",
          backgroundSize: "120px 100%",
        }}
      />
      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <div className="max-w-[60ch] mb-14">
          <div className="eyebrow mb-5 text-teal">The numbers</div>
          <h2 className="h-display text-[36px] sm:text-[46px] md:text-[60px] text-cream max-w-[18ch] leading-[1.02]">
            The rules of UAE claim recovery,{" "}
            <span className="italic font-normal text-teal">rewritten.</span>
          </h2>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/5">
          {stats.map((s, i) => (
            <StatTile key={s.label} value={s.value} label={s.label} delay={i * 0.1} />
          ))}
        </div>
      </div>
    </section>
  );
}

function StatTile({
  value,
  label,
  delay,
}: {
  value: string;
  label: string;
  delay: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 22 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className="bg-ink p-8 md:p-10 min-h-[180px] flex flex-col justify-between"
    >
      <div className="h-display text-[44px] sm:text-[56px] md:text-[64px] text-teal leading-none">
        {value}
      </div>
      <div className="mt-6 text-[13px] md:text-[14px] text-cream/65 leading-[1.5] max-w-[28ch]">
        {label}
      </div>
    </motion.div>
  );
}
