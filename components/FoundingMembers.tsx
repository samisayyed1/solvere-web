"use client";

import { motion } from "framer-motion";

const terms = [
  "Lifetime locked rate — never reprices",
  "Direct founder access for issues + escalation",
  "First-look at every new payer integration",
  "Priority on the recovery queue",
];

export default function FoundingMembers() {
  return (
    <section id="founding" className="bg-cream-deep border-y border-rule py-20 md:py-28">
      <div className="mx-auto max-w-container px-6 lg:px-10 grid grid-cols-1 lg:grid-cols-2 gap-14 lg:gap-20 items-start">
        <div>
          <div className="eyebrow eyebrow-amber mb-5 inline-flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-amber" />
            Founding members
          </div>
          <h2 className="h-serif text-[34px] sm:text-[44px] md:text-[56px] text-ink leading-[1.02] mb-6">
            Ten clinics. Locked-in pricing for the{" "}
            <span className="italic text-teal">lifetime of the contract.</span>
          </h2>
          <p className="text-[16px] md:text-[17px] text-muted leading-[1.6] max-w-[55ch]">
            We're selecting ten UAE clinics as Solvere's founding cohort. The
            rate you sign at on day one stays at that rate forever. We'll take
            what we learn from your data and use it to build the rest of the
            recovery system in the open with you.
          </p>

          {/* CTA wrapper — flip `false` → `true` to re-enable */}
          {false && (
            <div className="mt-10 flex flex-col sm:flex-row gap-3 sm:items-center">
              <a
                href="#final-cta"
                className="group inline-flex items-center justify-between gap-3 rounded-full bg-ink text-cream pl-6 pr-2 py-2.5 text-[15px] font-medium hover:bg-teal-deep transition-colors"
              >
                Apply to the founding cohort
                <span className="grid place-items-center w-9 h-9 rounded-full bg-cream text-ink transition-transform group-hover:translate-x-0.5">
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <path d="M1 6.5h11M7 2.5l4.5 4-4.5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
                  </svg>
                </span>
              </a>
            </div>
          )}
          {/* caption — flip `false` → `true` to re-enable */}
          {false && (
            <div className="mt-4 text-[11px] tracking-[0.22em] uppercase text-muted">
              Spots remaining: limited
            </div>
          )}
        </div>

        <div className="relative">
          {/* counter card */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.6 }}
            className="rounded-2xl border border-rule bg-cream p-7 md:p-9 mb-4"
          >
            <div className="flex items-center justify-between mb-6">
              <span className="text-[11px] tracking-[0.22em] uppercase text-muted">
                Cohort allocation
              </span>
              <span className="text-[11px] tracking-[0.22em] uppercase text-amber">
                2026 · Q2
              </span>
            </div>
            <div className="flex items-baseline gap-3 mb-6">
              <span className="h-display text-[64px] md:text-[80px] text-ink leading-none tabular-nums">10</span>
              <span className="h-serif text-[18px] text-muted pb-2">founding seats</span>
            </div>
            <div className="grid grid-cols-10 gap-1.5">
              {Array.from({ length: 10 }).map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 0.3 + i * 0.05 }}
                  className={`h-10 rounded ${
                    i < 3 ? "bg-teal" : "bg-rule"
                  }`}
                />
              ))}
            </div>
            <div className="mt-4 flex justify-between text-[11px] tracking-[0.18em] uppercase text-muted">
              <span><span className="text-teal">3</span> claimed</span>
              <span>7 remaining</span>
            </div>
          </motion.div>

          <div className="rounded-2xl border border-rule bg-cream p-7 md:p-8">
            <div className="text-[11px] tracking-[0.22em] uppercase text-muted mb-5">
              What founding seats unlock
            </div>
            <ul className="space-y-3">
              {terms.map((t, i) => (
                <motion.li
                  key={t}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.08 }}
                  className="flex items-start gap-3 text-[15px] text-ink-soft"
                >
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-teal flex-none" />
                  {t}
                </motion.li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
