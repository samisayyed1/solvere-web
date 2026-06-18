"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

const tabs = [
  {
    no: "01",
    key: "TRIAGE",
    label: "AI reads every denial",
    title: "AI reads every denied claim.",
    body:
      "Classification, reason coding, recoverability scoring across hundreds of claims at once. The work that used to take a biller a week happens in minutes — without missing anything that pays.",
    illustration: "funnel" as const,
  },
  {
    no: "02",
    key: "VERIFICATION",
    label: "A licensed coder approves",
    title: "A DHA-licensed coder verifies before submission.",
    body:
      "Every high-value or complex claim is reviewed by a UAE-licensed medical coder before it goes back to the payer. The human gate before the payer gateway. Nothing leaves the building unchecked.",
    illustration: "check" as const,
  },
  {
    no: "03",
    key: "EXECUTION",
    label: "Every payer's portal",
    title: "End-to-end through every payer portal.",
    body:
      "Resubmission and appeal through eClaimLink, Daman, Thiqa, NEXtCARE, NAS, MedNet, ADNIC, Sukoon and the rest. Documentation, follow-up, escalation — handled to outcome, not just to send.",
    illustration: "nodes" as const,
  },
  {
    no: "04",
    key: "LEARNING",
    label: "Every recovery trains the next",
    title: "The system gets sharper every cycle.",
    body:
      "Each payer response updates the rule library. After ten thousand claims, our denial-reason knowledge becomes the moat: nobody else in the GCC can rebuild it quickly.",
    illustration: "bars" as const,
  },
];

export default function AIDeepDive() {
  const [active, setActive] = useState(0);
  const tab = tabs[active];

  return (
    <section id="deep-dive" className="relative bg-ink text-cream py-20 md:py-28 grain overflow-hidden">
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.06] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />
      <div className="relative mx-auto max-w-container px-6 lg:px-10">
        <div className="max-w-[60ch] mb-12">
          <div className="eyebrow mb-5 text-teal">Under the hood</div>
          <h2 className="h-display text-[34px] sm:text-[44px] md:text-[56px] text-cream leading-[1.02] mb-5">
            AI-native recovery,{" "}
            <span className="italic font-normal text-teal">human-verified.</span>
          </h2>
          <p className="text-[16px] md:text-[17px] text-cream/65 leading-[1.6]">
            Pure-AI vendors miss what the rules don't cover. Pure-human shops
            can't scale. Solvere ships both, in the same loop.
          </p>
        </div>

        {/* tab strip */}
        <div className="flex flex-wrap gap-2 mb-10">
          {tabs.map((t, i) => (
            <button
              key={t.no}
              onClick={() => setActive(i)}
              className={`group relative rounded-full px-4 py-2 text-[12px] tracking-[0.18em] uppercase border transition-all ${
                active === i
                  ? "bg-teal/20 border-teal/40 text-cream"
                  : "bg-transparent border-white/10 text-cream/55 hover:border-white/25 hover:text-cream"
              }`}
            >
              <span className="text-teal/90 mr-2">{t.no}</span>
              {t.key}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1.05fr_1fr] gap-10 lg:gap-16 items-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={tab.no}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            >
              <h3 className="h-serif text-[28px] sm:text-[34px] md:text-[42px] text-cream leading-[1.1] mb-6">
                {tab.title}
              </h3>
              <p className="text-[16px] md:text-[18px] text-cream/65 leading-[1.6] max-w-[52ch]">
                {tab.body}
              </p>

              <div className="mt-8 flex items-center gap-4">
                <button
                  onClick={() => setActive((active - 1 + tabs.length) % tabs.length)}
                  className="w-10 h-10 rounded-full border border-white/15 grid place-items-center hover:bg-white/5"
                  aria-label="Previous tab"
                >
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <path d="M12 6.5H1M5 2.5L1 6.5l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
                  </svg>
                </button>
                <button
                  onClick={() => setActive((active + 1) % tabs.length)}
                  className="w-10 h-10 rounded-full border border-white/15 grid place-items-center hover:bg-white/5"
                  aria-label="Next tab"
                >
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <path d="M1 6.5h11M7 2.5l4.5 4-4.5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
                  </svg>
                </button>
                <span className="text-[12px] tracking-[0.18em] uppercase text-cream/45">
                  {active + 1} / {tabs.length}
                </span>
              </div>
            </motion.div>
          </AnimatePresence>

          <div className="relative aspect-square max-w-[480px] w-full justify-self-center lg:justify-self-end">
            <AnimatePresence mode="wait">
              <motion.div
                key={tab.illustration}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                className="absolute inset-0 rounded-3xl border border-white/8 bg-ink-soft/40 backdrop-blur"
              >
                <Illustration kind={tab.illustration} />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}

function Illustration({ kind }: { kind: "funnel" | "check" | "nodes" | "bars" }) {
  if (kind === "funnel") {
    const rows = 9;
    return (
      <div className="absolute inset-0 grid place-items-center">
        <svg viewBox="0 0 400 400" className="w-[78%] h-[78%]" fill="none">
          {Array.from({ length: rows }).map((_, r) => {
            const cols = rows - r;
            const y = 60 + r * 32;
            const startX = 200 - cols * 16;
            return Array.from({ length: cols }).map((_, c) => {
              const cx = startX + c * 32 + 16;
              const isHit = (c + r) % 3 !== 0;
              return (
                <motion.circle
                  key={`${r}-${c}`}
                  cx={cx}
                  cy={y}
                  r={3.5}
                  fill={isHit ? "#0E5E5E" : "rgba(255,255,255,0.18)"}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.4, delay: (r * 0.06) + (c * 0.02) }}
                />
              );
            });
          })}
          <motion.path
            d="M120 60 L200 360 L280 60"
            stroke="rgba(14,94,94,0.4)"
            strokeWidth="1"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.4, ease: "easeInOut" }}
          />
        </svg>
      </div>
    );
  }
  if (kind === "check") {
    return (
      <div className="absolute inset-0 grid place-items-center">
        <svg viewBox="0 0 400 400" className="w-[68%] h-[68%]" fill="none">
          <rect x="80" y="60" width="240" height="280" rx="12" stroke="rgba(255,255,255,0.15)" />
          {[110, 140, 170, 200, 230, 260].map((y, i) => (
            <motion.rect
              key={y}
              x="100"
              y={y}
              width={i === 5 ? 130 : 200}
              height="6"
              rx="3"
              fill="rgba(255,255,255,0.18)"
              initial={{ scaleX: 0, originX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
            />
          ))}
          <motion.circle
            cx="280"
            cy="290"
            r="42"
            fill="rgba(14,94,94,0.18)"
            stroke="#0E5E5E"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.6, type: "spring", stiffness: 200, damping: 14 }}
          />
          <motion.path
            d="M260 290 l15 15 l25 -28"
            stroke="#0E5E5E"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 0.8, duration: 0.4 }}
          />
        </svg>
      </div>
    );
  }
  if (kind === "nodes") {
    return (
      <div className="absolute inset-0 grid place-items-center">
        <svg viewBox="0 0 400 400" className="w-[80%] h-[80%]" fill="none">
          {/* center */}
          <motion.circle
            cx="200" cy="200" r="32"
            fill="rgba(14,94,94,0.25)"
            stroke="#0E5E5E"
            initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ duration: 0.5 }}
          />
          <text x="200" y="206" textAnchor="middle" fontSize="11" fill="#F8F6F1" fontFamily="sans-serif">SOLVERE</text>
          {[
            { x: 60, y: 80, l: "DAMAN" },
            { x: 340, y: 80, l: "THIQA" },
            { x: 30, y: 220, l: "NAS" },
            { x: 370, y: 220, l: "MEDNET" },
            { x: 100, y: 360, l: "NEXtCARE" },
            { x: 300, y: 360, l: "ADNIC" },
          ].map((n, i) => (
            <g key={n.l}>
              <motion.line
                x1="200" y1="200" x2={n.x} y2={n.y}
                stroke="rgba(14,94,94,0.45)"
                strokeWidth="1"
                strokeDasharray="3 3"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ delay: 0.2 + i * 0.08, duration: 0.6 }}
              />
              <motion.circle
                cx={n.x} cy={n.y} r="18"
                fill="rgba(255,255,255,0.04)"
                stroke="rgba(255,255,255,0.25)"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.4 + i * 0.08 }}
              />
              <text x={n.x} y={n.y + 36} textAnchor="middle" fontSize="9" fill="rgba(248,246,241,0.6)" fontFamily="sans-serif" letterSpacing="1.5">{n.l}</text>
            </g>
          ))}
        </svg>
      </div>
    );
  }
  // bars
  return (
    <div className="absolute inset-0 grid place-items-center">
      <svg viewBox="0 0 400 400" className="w-[80%] h-[80%]" fill="none">
        <line x1="60" y1="340" x2="360" y2="340" stroke="rgba(255,255,255,0.15)" />
        <line x1="60" y1="340" x2="60" y2="80" stroke="rgba(255,255,255,0.15)" />
        {[60, 100, 140, 180, 220, 260, 300, 340].slice(0, 7).map((h, i) => (
          <motion.rect
            key={i}
            x={80 + i * 38}
            y={340 - h}
            width="22"
            height={h}
            fill={i === 6 ? "#0E5E5E" : `rgba(14,94,94,${0.25 + i * 0.08})`}
            initial={{ scaleY: 0, originY: 1 }}
            animate={{ scaleY: 1 }}
            transition={{ duration: 0.6, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] }}
            style={{ transformOrigin: `center ${340}px` }}
          />
        ))}
        <motion.path
          d="M91 280 L129 240 L167 210 L205 180 L243 150 L281 120 L319 90"
          stroke="rgba(14,94,94,0.6)"
          strokeWidth="1.5"
          strokeDasharray="4 4"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.2, delay: 0.6 }}
        />
      </svg>
    </div>
  );
}
