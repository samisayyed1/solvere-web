"use client";

import { motion } from "framer-motion";

const fade = {
  hidden: { opacity: 0, y: 18 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.8, delay: 0.1 + i * 0.08, ease: [0.22, 1, 0.36, 1] },
  }),
};

export default function Hero() {
  return (
    <section
      id="top"
      className="relative pt-32 md:pt-40 pb-20 md:pb-28 overflow-hidden"
    >
      {/* ambient teal bloom */}
      <div
        aria-hidden
        className="absolute -top-40 -left-40 w-[820px] h-[820px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(14,94,94,0.10), rgba(14,94,94,0) 70%)",
        }}
      />
      <div
        aria-hidden
        className="absolute top-10 right-0 w-[640px] h-[640px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(180,83,9,0.06), rgba(180,83,9,0) 70%)",
        }}
      />

      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <motion.div
          variants={fade}
          custom={0}
          initial="hidden"
          animate="show"
          className="eyebrow inline-flex items-center gap-2 mb-7"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-teal" />
          ABU DHABI · UNITED ARAB EMIRATES
        </motion.div>

        <motion.h1
          variants={fade}
          custom={1}
          initial="hidden"
          animate="show"
          className="h-display text-[44px] leading-[1] sm:text-[60px] md:text-[76px] lg:text-[88px] text-ink max-w-[16ch]"
        >
          A new standard for{" "}
          <span className="relative inline-block">
            <span className="relative z-10 text-teal">UAE claim recovery</span>
            <span
              aria-hidden
              className="absolute inset-x-0 bottom-1 h-[0.35em] bg-teal/10 -skew-y-1"
            />
          </span>
          .
        </motion.h1>

        <motion.p
          variants={fade}
          custom={2}
          initial="hidden"
          animate="show"
          className="mt-8 max-w-[58ch] text-[18px] md:text-[20px] leading-[1.55] text-muted"
        >
          Solvere uses AI agents and a DHA-licensed medical coder to recover the
          denied insurance claims your billers gave up on — end to end, every
          payer, pay only on recovery.
        </motion.p>

        <motion.div
          variants={fade}
          custom={3}
          initial="hidden"
          animate="show"
          className="mt-10 flex flex-col sm:flex-row gap-3 sm:items-center"
        >
          <a
            href="#final-cta"
            className="group inline-flex items-center justify-between gap-3 rounded-full bg-ink text-cream pl-6 pr-2 py-2.5 text-[15px] font-medium hover:bg-teal-deep transition-colors"
          >
            Book a 20-minute audit call
            <span className="grid place-items-center w-9 h-9 rounded-full bg-cream text-ink transition-transform group-hover:translate-x-0.5">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                <path
                  d="M1 6.5h11M7 2.5l4.5 4-4.5 4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="square"
                />
              </svg>
            </span>
          </a>
          <a
            href="#how"
            className="inline-flex items-center gap-2 rounded-full border border-ink/15 text-ink px-6 py-2.5 text-[15px] font-medium hover:border-ink hover:bg-ink hover:text-cream transition-all"
          >
            See how it works
          </a>
        </motion.div>

        <motion.div
          variants={fade}
          custom={4}
          initial="hidden"
          animate="show"
          className="mt-10 flex items-center gap-3 text-[12px] uppercase tracking-[0.18em] text-muted"
        >
          <Pill>No software</Pill>
          <Pill>No integration</Pill>
          <Pill>Pay only on recovery</Pill>
        </motion.div>
      </div>
    </section>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="w-1 h-1 rounded-full bg-teal" />
      {children}
    </span>
  );
}
