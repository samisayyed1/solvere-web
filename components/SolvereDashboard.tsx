"use client";

import { motion, useInView, AnimatePresence } from "framer-motion";
import { useEffect, useRef, useState } from "react";

type Card = {
  payer: string;
  amount: string;
  reason: string;
  id: string;
  paid?: boolean;
};

const columns: { title: string; status: string; cards: Card[]; total: string }[] = [
  {
    title: "Received",
    status: "Inbound",
    total: "AED 32,500",
    cards: [
      { payer: "NAS", amount: "AED 4,200", reason: "Eligibility lapse", id: "DM-24891" },
      { payer: "MedNet", amount: "AED 3,100", reason: "Code specificity", id: "DM-24827" },
      { payer: "Daman", amount: "AED 18,400", reason: "Bundling rule", id: "DM-24814" },
      { payer: "NEXtCARE", amount: "AED 6,800", reason: "Prior auth missing", id: "DM-24802" },
    ],
  },
  {
    title: "In review",
    status: "Triage",
    total: "AED 25,800",
    cards: [
      { payer: "Daman", amount: "AED 12,800", reason: "Documentation insufficient", id: "DM-24773" },
      { payer: "ADNIC", amount: "AED 7,200", reason: "CPT–ICD mismatch", id: "DM-24759" },
      { payer: "Thiqa", amount: "AED 5,800", reason: "Filing deadline", id: "DM-24744" },
      { payer: "MedNet", amount: "AED 8,900", reason: "Modifier review", id: "DM-24738" },
    ],
  },
  {
    title: "Resubmitted",
    status: "With payer",
    total: "AED 35,800",
    cards: [
      { payer: "Thiqa", amount: "AED 8,400", reason: "Resubmitted with fix", id: "DM-24712" },
      { payer: "Daman", amount: "AED 22,500", reason: "Appeal filed", id: "DM-24698" },
      { payer: "NAS", amount: "AED 4,900", reason: "Awaiting payer response", id: "DM-24681" },
      { payer: "ADNIC", amount: "AED 14,300", reason: "Escalation pending", id: "DM-24675" },
    ],
  },
  {
    title: "Recovered",
    status: "Paid",
    total: "AED 45,500",
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
  const [pulseCol, setPulseCol] = useState<number>(-1);

  // gentle pulse cycling through columns to imply live movement
  useEffect(() => {
    if (!inView) return;
    let i = 0;
    const id = setInterval(() => {
      setPulseCol(i);
      i = (i + 1) % columns.length;
    }, 1800);
    return () => clearInterval(id);
  }, [inView]);

  return (
    <section
      id="dashboard"
      className="relative bg-ink text-cream py-20 md:py-28 overflow-hidden grain"
    >
      {/* hairline grid backdrop */}
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.06] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
        }}
      />
      <div
        aria-hidden
        className="absolute -top-32 right-0 w-[700px] h-[700px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(14,94,94,0.32), rgba(14,94,94,0) 70%)",
        }}
      />

      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <div className="flex items-end justify-between flex-wrap gap-6 mb-12">
          <div>
            <div className="eyebrow inline-flex items-center gap-2 mb-5 text-teal">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-75 animate-ping" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-teal" />
              </span>
              INSIDE SOLVERE
            </div>
            <h2 className="h-display text-[34px] sm:text-[44px] md:text-[56px] max-w-[14ch] text-cream leading-[1.02]">
              See claims move through Solvere.
            </h2>
            <p className="mt-5 max-w-[58ch] text-[16px] md:text-[17px] text-cream/65 leading-[1.55]">
              Every denied claim moves through four stages. AI agents triage, a
              DHA-licensed coder verifies, payer portals receive the
              resubmission, the wire lands. You see all of it.
            </p>
          </div>

        </div>

        <div
          ref={ref}
          className="relative rounded-2xl border bg-ink-soft/40 p-4 md:p-6 backdrop-blur"
          style={{ borderColor: "rgba(255,255,255,0.08)" }}
        >
          {/* chrome */}
          <div className="flex items-center justify-between px-2 pb-4 mb-2 border-b border-white/8">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-white/12" />
                <span className="w-2.5 h-2.5 rounded-full bg-white/12" />
                <span className="w-2.5 h-2.5 rounded-full bg-white/12" />
              </div>
              <span className="ml-2 text-[12px] tracking-wide text-cream/55 font-mono">
                solvere.app · clinic-recovery-board
              </span>
            </div>
            <div className="hidden md:flex items-center gap-5 text-[11px] tracking-[0.18em] uppercase text-cream/45">
              <span className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-teal animate-pulse" />
                Live ledger
              </span>
              <span className="text-cream/25">/</span>
              <span>Q2 · 2026</span>
              <span className="text-cream/25">/</span>
              <span>Updated 2m ago</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-white/5 rounded-xl overflow-hidden">
            {columns.map((col, colIdx) => (
              <Column
                key={col.title}
                col={col}
                colIdx={colIdx}
                inView={inView}
                pulse={pulseCol === colIdx}
              />
            ))}
          </div>

          {/* footer strip */}
          <div className="mt-5 px-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-[11px] tracking-[0.18em] uppercase text-cream/50">
            <SummaryStat label="Claims tracked" value="16" />
            <SummaryStat label="In motion" value="AED 94,100" />
            <SummaryStat label="Recovered (30d)" value="AED 45,500" />
            <SummaryStat label="Recovery rate" value="62%" highlight />
          </div>
        </div>

        <p className="mt-7 text-[13px] text-cream/55 max-w-[60ch] leading-[1.55]">
          Real claims move in real time once Solvere is running. This is the
          view you receive monthly.
        </p>
      </div>
    </section>
  );
}

function Column({
  col,
  colIdx,
  inView,
  pulse,
}: {
  col: { title: string; status: string; total: string; cards: Card[] };
  colIdx: number;
  inView: boolean;
  pulse: boolean;
}) {
  return (
    <div className="bg-ink p-4 md:p-5 flex flex-col min-h-[560px]">
      <div className="flex items-baseline justify-between mb-5">
        <div className="flex items-baseline gap-2">
          <h3 className="h-serif text-[17px] text-cream">{col.title}</h3>
          <span className="text-[11px] text-cream/45 tabular-nums">
            {col.cards.length}
          </span>
        </div>
        <span className="flex items-center gap-1.5 text-[10px] tracking-[0.18em] uppercase text-cream/45">
          <AnimatePresence>
            {pulse && (
              <motion.span
                key="pulse"
                initial={{ opacity: 0, scale: 0.6 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="w-1 h-1 rounded-full bg-teal"
              />
            )}
          </AnimatePresence>
          {col.status}
        </span>
      </div>

      <div className="flex flex-col gap-2.5 flex-1">
        {col.cards.map((card, i) => (
          <motion.div
            key={card.id}
            initial={{ opacity: 0, y: 14, scale: 0.985 }}
            animate={
              inView
                ? { opacity: 1, y: 0, scale: 1 }
                : { opacity: 0, y: 14, scale: 0.985 }
            }
            transition={{
              duration: 0.5,
              delay: colIdx * 0.16 + i * 0.06,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="kanban-card rounded-lg p-3.5 transition-all hover:translate-y-[-1px]"
          >
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-2">
                <PayerDot payer={card.payer} />
                <span className="text-[12.5px] font-medium text-cream tracking-tight">
                  {card.payer}
                </span>
              </div>
              <span className="text-[10px] tracking-wider text-cream/30 font-mono">
                {card.id}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="h-display text-[17px] text-cream tabular-nums leading-none">
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
            <div className="mt-2.5 flex items-center gap-2 text-[11.5px] text-cream/55">
              <span
                className={`w-1 h-1 rounded-full ${
                  card.paid ? "bg-teal" : "bg-cream/30"
                }`}
              />
              <span className="truncate">{card.reason}</span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-white/8 flex items-center justify-between text-[11px] tracking-[0.16em] uppercase">
        <span className="text-cream/40">Total</span>
        <span className="text-cream tabular-nums text-[13px] tracking-normal font-medium">
          {col.total}
        </span>
      </div>
    </div>
  );
}

function PayerDot({ payer }: { payer: string }) {
  // a small monogrammed badge — uniform visual rhythm
  const initials = payer
    .replace(/[^a-zA-Z]/g, "")
    .slice(0, 2)
    .toUpperCase();
  return (
    <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-white/8 text-[9px] tracking-wider text-cream/75 font-medium">
      {initials}
    </span>
  );
}

function SummaryStat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span>{label}</span>
      <span
        className={`text-[15px] tracking-normal font-medium tabular-nums ${
          highlight ? "text-teal" : "text-cream"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
