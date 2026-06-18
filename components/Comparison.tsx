"use client";

import { motion } from "framer-motion";

const rows = [
  {
    cap: "End-to-end claim recovery (resubmission + appeal + follow-up)",
    diy: "Partial",
    solvere: true,
  },
  { cap: "AI triage of denied claims by reason and recoverability", diy: "—", solvere: true },
  { cap: "DHA-licensed medical coder verification on every claim", diy: "Depends", solvere: true },
  { cap: "Coverage across every major UAE payer portal", diy: "Manual", solvere: true },
  { cap: "Pay only on recovery (no upfront fee, no software cost)", diy: "—", solvere: true },
  { cap: "Software install or PMS integration required", diy: "Often", solvere: false, invert: true },
  { cap: "Free recoverability audit before any commitment", diy: "—", solvere: "24-hour" },
  { cap: "Direct founder access for issues and escalation", diy: "—", solvere: "Founding cohort" },
];

export default function Comparison() {
  return (
    <section className="bg-cream py-20 md:py-28 border-t border-rule">
      <div className="mx-auto max-w-container px-6 lg:px-10">
        <div className="max-w-[62ch] mb-12">
          <div className="eyebrow mb-5">How it compares</div>
          <h2 className="h-serif text-[36px] sm:text-[46px] md:text-[58px] text-ink leading-[1.02] mb-6">
            Solvere vs. doing it yourself.
          </h2>
          <p className="text-[17px] leading-[1.55] text-muted">
            The decision isn't whether to recover denied claims — you've already
            paid your biller to try. The decision is whether to chase the rest
            at marginal cost or write them off.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="rounded-2xl border border-rule overflow-hidden bg-cream-deep"
        >
          <div className="grid grid-cols-[1.6fr_1fr_1fr] bg-ink text-cream text-[11px] tracking-[0.18em] uppercase">
            <div className="px-6 py-4">Capability</div>
            <div className="px-6 py-4 border-l border-white/10">Doing it yourself</div>
            <div className="px-6 py-4 border-l border-white/10 text-teal">Solvere</div>
          </div>

          {rows.map((r, i) => (
            <motion.div
              key={r.cap}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.45, delay: i * 0.04 }}
              className={`grid grid-cols-[1.6fr_1fr_1fr] items-center border-t border-rule text-[14px] md:text-[15px] ${
                i % 2 === 1 ? "bg-cream" : ""
              }`}
            >
              <div className="px-6 py-5 text-ink-soft leading-[1.4]">{r.cap}</div>
              <div className="px-6 py-5 border-l border-rule text-muted">
                {r.diy}
              </div>
              <div className="px-6 py-5 border-l border-rule text-teal font-medium">
                {typeof r.solvere === "boolean"
                  ? r.solvere
                    ? r.invert
                      ? <Dash />
                      : <Check />
                    : r.invert
                    ? <Dash />
                    : <Dash />
                  : r.solvere}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

function Check() {
  return (
    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-teal/10 border border-teal/30">
      <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
        <path
          d="M1 5.5l3 3 6-6"
          stroke="#0E5E5E"
          strokeWidth="1.8"
          strokeLinecap="square"
        />
      </svg>
    </span>
  );
}
function Dash() {
  return <span className="text-muted">—</span>;
}
