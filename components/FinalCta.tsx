"use client";

import { motion } from "framer-motion";

export default function FinalCta() {
  return (
    <section
      id="final-cta"
      className="relative bg-ink text-cream py-24 md:py-36 overflow-hidden grain"
    >
      <div
        aria-hidden
        className="absolute -bottom-40 -left-40 w-[720px] h-[720px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(14,94,94,0.30), rgba(14,94,94,0) 70%)",
        }}
      />
      <div
        aria-hidden
        className="absolute -top-40 -right-40 w-[640px] h-[640px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(180,83,9,0.10), rgba(180,83,9,0) 70%)",
        }}
      />

      <div className="relative mx-auto max-w-container px-6 lg:px-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="eyebrow text-teal mb-7 inline-flex items-center gap-2"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-teal" />
          Start the recovery
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 22 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.05 }}
          className="h-display text-[44px] sm:text-[60px] md:text-[80px] text-cream max-w-[18ch] mx-auto leading-[1.02]"
        >
          Ready to recover what your clinic is{" "}
          <span className="italic font-normal text-teal">owed?</span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="mt-7 text-[17px] md:text-[19px] text-cream/65 max-w-[58ch] mx-auto leading-[1.55]"
        >
          Send us your last ninety days of denials. We'll return a
          recoverability audit in five working days. No software. No upfront
          fee. No risk.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.25 }}
          className="mt-12"
        >
          <a
            href="mailto:hello@solvere.ai?subject=Audit%20call"
            className="group inline-flex items-center justify-between gap-3 rounded-full bg-teal hover:bg-teal-deep text-cream pl-7 pr-2 py-3 text-[16px] font-medium transition-colors"
          >
            Book a 20-minute audit call
            <span className="grid place-items-center w-10 h-10 rounded-full bg-cream text-ink transition-transform group-hover:translate-x-0.5">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1 7h12M7.5 2l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
              </svg>
            </span>
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.45 }}
          className="mt-12 inline-flex items-center gap-6 text-[11px] tracking-[0.22em] uppercase text-cream/55"
        >
          <span className="flex items-center gap-2"><Dot /> 5-day audit</span>
          <span className="text-cream/20">·</span>
          <span className="flex items-center gap-2"><Dot /> Pay only on recovery</span>
          <span className="text-cream/20">·</span>
          <span className="flex items-center gap-2"><Dot /> Zero risk</span>
        </motion.div>
      </div>
    </section>
  );
}

function Dot() {
  return <span className="w-1 h-1 rounded-full bg-teal" />;
}
