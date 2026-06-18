"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

type Card = {
  payer: string;
  amount: string;
  reason: string;
  id: string;
  paid?: boolean;
};

const columns: { title: string; status: string; cards: Card[] }[] = [
  {
    title: "Received",
    status: "INBOUND",
    cards: [
      { payer: "NAS", amount: "AED 4,200", reason: "Eligibility lapse", id: "DM-24891" },
      { payer: "MedNet", amount: "AED 3,100", reason: "Code specificity", id: "DM-24827" },
      { payer: "Daman", amount: "AED 18,400", reason: "Bundling rule", id: "DM-24814" },
      { payer: "NEXtCARE", amount: "AED 6,800", reason: "Prior auth missing", id: "DM-24802" },
    ],
  },
  {
    title: "In review",
    status: "TRIAGE",
    cards: [
      { payer: "Daman", amount: "AED 12,800", reason: "Documentation insufficient", id: "DM-24773" },
      { payer: "ADNIC", amount: "AED 7,200", reason: "CPT–ICD mismatch", id: "DM-24759" },
      { payer: "Thiqa", amount: "AED 5,800", reason: "Filing deadline", id: "DM-24744" },
    ],
  },
  {
    title: "Resubmitted",
    status: "WITH PAYER",
    cards: [
      { payer: "Thiqa", amount: "AED 8,400", reason: "Resubmitted with fix", id: "DM-24712" },
      { payer: "Daman", amount: "AED 22,500", reason: "Appeal filed", id: "DM-24698" },
      { payer: "NAS", amount: "AED 4,900", reason: "Awaiting payer response", id: "DM-24681" },
    ],
  },
  {
    title: "Recovered",
    status: "PAID",
    cards: [
      { payer: "NEXtCARE", amount: "AED 6,100", reason: "Paid in full", id: "DM-24612", paid: true },
      { payer: "Daman", amount: "AED 18,900", reason: "Paid in full", id: "DM-24587", paid: true },
      { payer: "MedNet", amount: "AED 9,300", reason: "Paid (partial appeal)", id: "DM-24574", paid: true },
      { payer: "Thiqa", amount: "AED 11,200", reason: "Paid in full", id: "DM-24561", paid: true },
    ],
  },
];

export default function SolvereDashboard() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section
      id="dashboard"
      className="relative bg-ink text-cream py-20 md:py-28 overflow-hidden grain"
    >
      {/* hairline grid backdrop */}
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.08] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.6) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
        }}
      />
      <div
        aria-hidden
        className="absolute -top-32 right-0 w-[700px] h-[700px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(14,94,94,0.35), rgba(14,94,94,0) 70%)",
        }}
      />

      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <div className="flex items-end justify-between flex-wrap gap-6 mb-10">
          <div>
            <div className="eyebrow inline-flex items-center gap-2 mb-5 text-teal">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-75 animate-ping" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-teal" />
              </span>
              INSIDE SOLVERE
            </div>
            <h2 className="h-display text-[34px] sm:text-[44px] md:text-[56px] max-w-[14ch] text-cream">
              See claims move through Solvere.
            </h2>
            <p className="mt-5 max-w-[58ch] text-[16px] md:text-[17px] text-cream/65 leading-[1.55]">
              Every denied claim moves through four stages. AI agents triage, a
              DHA-licensed coder verifies, payer portals receive the
              resubmission, the wire lands. You see all of it.
            </p>
          </div>

          <div className="inline-flex items-center gap-2 rounded-full border border-amber/40 bg-amber/10 px-3 py-1.5 text-[11px] uppercase tracking-[0.18em] text-amber">
            <span className="w-1.5 h-1.5 rounded-full bg-amber" />
            Sample · Illustrative
          </div>
        </div>

        <div
          ref={ref}
          className="relative rounded-2xl border border-white/8 bg-ink-soft/40 p-3 md:p-5 backdrop-blur"
          style={{ borderColor: "rgba(255,255,255,0.08)" }}
        >
          {/* dashboard chrome */}
          <div className="flex items-center justify-between px-3 py-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
              <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
              <span className="w-2.5 h-2.5 rounded-full bg-white/15" />
              <span className="ml-3 text-[12px] tracking-wide text-cream/55">
                solvere.app · clinic-recovery-board
              </span>
            </div>
            <div className="hidden md:flex items-center gap-4 text-[11px] text-cream/45 uppercase tracking-[0.18em]">
              <span>Q2 · 2026</span>
              <span className="text-cream/30">/</span>
              <span>Updated 2m ago</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
            {columns.map((col, colIdx) => (
              <div key={col.title} className="min-h-[420px]">
                <div className="flex items-baseline justify-between mb-3 px-2">
                  <div className="flex items-baseline gap-2">
                    <h3 className="h-serif text-[18px] text-cream">
                      {col.title}
                    </h3>
                    <span className="text-[11px] text-cream/40 tabular-nums">
                      {col.cards.length}
                    </span>
                  </div>
                  <span className="text-[10px] tracking-[0.18em] text-cream/40">
                    {col.status}
                  </span>
                </div>

                <div className="flex flex-col gap-2.5">
                  {col.cards.map((card, i) => (
                    <motion.div
                      key={card.id}
                      initial={{ opacity: 0, y: 18, scale: 0.98 }}
                      animate={
                        inView
                          ? { opacity: 1, y: 0, scale: 1 }
                          : { opacity: 0, y: 18, scale: 0.98 }
                      }
                      transition={{
                        duration: 0.5,
                        delay: colIdx * 0.18 + i * 0.08,
                        ease: [0.22, 1, 0.36, 1],
                      }}
                      className="kanban-card rounded-xl p-3.5 group transition-all"
                    >
                      <div className="flex items-baseline justify-between">
                        <span className="text-[13px] font-medium text-cream">
                          {card.payer}
                        </span>
                        <span className="text-[10px] tracking-wider text-cream/35 font-mono">
                          {card.id}
                        </span>
                      </div>
                      <div className="mt-2 flex items-center gap-2">
                        <span className="h-display text-[18px] text-cream tabular-nums">
                          {card.amount}
                        </span>
                        {card.paid && (
                          <span className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-teal/20 border border-teal/40">
                            <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                              <path
                                d="M1 4l2 2 4-4"
                                stroke="#0E5E5E"
                                strokeWidth="1.8"
                                strokeLinecap="square"
                              />
                            </svg>
                          </span>
                        )}
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-[12px] text-cream/55">
                        <span
                          className={`w-1 h-1 rounded-full ${
                            card.paid ? "bg-teal" : "bg-cream/30"
                          }`}
                        />
                        {card.reason}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* bottom strip */}
          <div className="mt-6 border-t border-white/5 pt-4 px-2 flex items-center justify-between text-[11px] tracking-[0.18em] uppercase text-cream/40">
            <span>14 claims tracked · AED 140,400 in motion</span>
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse" />
              Live ledger
            </span>
          </div>
        </div>

        <p className="mt-6 text-[13px] text-cream/55 max-w-[60ch] leading-[1.55]">
          Real claims move in real time once Solvere is running. This is the
          view you receive monthly.
        </p>
      </div>
    </section>
  );
}
