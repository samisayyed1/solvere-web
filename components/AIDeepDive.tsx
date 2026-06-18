"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const AUTO_MS = 6000;

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
  const [paused, setPaused] = useState(false);
  const [cycleKey, setCycleKey] = useState(0);
  const sectionRef = useRef<HTMLDivElement>(null);
  const tab = tabs[active];

  // auto-advance: increments active every AUTO_MS; resets on user interaction
  useEffect(() => {
    if (paused) return;
    const id = setTimeout(() => {
      setActive((a) => (a + 1) % tabs.length);
      setCycleKey((k) => k + 1);
    }, AUTO_MS);
    return () => clearTimeout(id);
  }, [active, paused, cycleKey]);

  // pause when user hovers / focuses
  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const enter = () => setPaused(true);
    const leave = () => setPaused(false);
    el.addEventListener("mouseenter", enter);
    el.addEventListener("mouseleave", leave);
    el.addEventListener("focusin", enter);
    el.addEventListener("focusout", leave);
    return () => {
      el.removeEventListener("mouseenter", enter);
      el.removeEventListener("mouseleave", leave);
      el.removeEventListener("focusin", enter);
      el.removeEventListener("focusout", leave);
    };
  }, []);

  // pause when section is offscreen
  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => setPaused((p) => (entry.isIntersecting ? p : true)),
      { threshold: 0.3 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const go = (i: number) => {
    setActive(i);
    setCycleKey((k) => k + 1);
  };

  return (
    <section
      id="deep-dive"
      ref={sectionRef}
      className="relative bg-ink text-cream py-20 md:py-28 grain overflow-hidden"
    >
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

        {/* tab strip with auto-progress fill */}
        <div className="flex flex-wrap gap-2 mb-10">
          {tabs.map((t, i) => (
            <button
              key={t.no}
              onClick={() => go(i)}
              className={`relative overflow-hidden rounded-full px-4 py-2 text-[12px] tracking-[0.18em] uppercase border transition-colors ${
                active === i
                  ? "bg-teal/15 border-teal/40 text-cream"
                  : "bg-transparent border-white/10 text-cream/55 hover:border-white/25 hover:text-cream"
              }`}
            >
              {active === i && (
                <motion.span
                  key={`progress-${i}-${cycleKey}-${paused ? "p" : "r"}`}
                  aria-hidden
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: paused ? 0 : 1 }}
                  transition={{
                    duration: paused ? 0 : AUTO_MS / 1000,
                    ease: "linear",
                  }}
                  className="absolute inset-y-0 left-0 right-0 bg-teal/20 origin-left"
                />
              )}
              <span className="relative">
                <span className="text-teal/90 mr-2">{t.no}</span>
                {t.key}
              </span>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-12 items-stretch">
          {/* TEXT COLUMN — fixed min height to match diagram */}
          <div className="relative min-h-[460px] flex flex-col">
            <AnimatePresence mode="wait">
              <motion.div
                key={tab.no}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                className="flex-1 flex flex-col"
              >
                <div className="text-[10px] tracking-[0.22em] uppercase text-cream/40 mb-5 flex items-center gap-3">
                  <span className="text-teal">{tab.no}</span>
                  <span className="w-8 h-px bg-white/15" />
                  <span>{tab.key}</span>
                </div>
                <h3 className="h-serif text-[28px] sm:text-[34px] md:text-[42px] text-cream leading-[1.08] mb-6 max-w-[18ch]">
                  {tab.title}
                </h3>
                <p className="text-[16px] md:text-[17px] text-cream/65 leading-[1.65] max-w-[52ch]">
                  {tab.body}
                </p>
              </motion.div>
            </AnimatePresence>

            {/* controls + counter pinned bottom */}
            <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => go((active - 1 + tabs.length) % tabs.length)}
                  className="w-10 h-10 rounded-full border border-white/15 grid place-items-center hover:bg-white/5 hover:border-white/30 transition-colors"
                  aria-label="Previous"
                >
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <path
                      d="M12 6.5H1M5 2.5L1 6.5l4 4"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="square"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => go((active + 1) % tabs.length)}
                  className="w-10 h-10 rounded-full border border-white/15 grid place-items-center hover:bg-white/5 hover:border-white/30 transition-colors"
                  aria-label="Next"
                >
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <path
                      d="M1 6.5h11M7 2.5l4.5 4-4.5 4"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="square"
                    />
                  </svg>
                </button>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[11px] tracking-[0.18em] uppercase text-cream/45 tabular-nums">
                  {String(active + 1).padStart(2, "0")} / {String(tabs.length).padStart(2, "0")}
                </span>
                <span className="flex items-center gap-1.5 text-[10px] tracking-[0.18em] uppercase text-cream/35">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      paused ? "bg-amber" : "bg-teal animate-pulse"
                    }`}
                  />
                  {paused ? "Paused" : "Auto"}
                </span>
              </div>
            </div>
          </div>

          {/* DIAGRAM COLUMN — same min-height */}
          <div className="relative min-h-[460px] rounded-3xl border border-white/8 bg-ink-soft/40 backdrop-blur overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={tab.illustration}
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                className="absolute inset-0"
              >
                <Illustration kind={tab.illustration} />
              </motion.div>
            </AnimatePresence>
            {/* mini caption pinned bottom of diagram */}
            <div className="absolute bottom-4 left-5 right-5 flex items-center justify-between text-[10px] tracking-[0.22em] uppercase text-cream/35">
              <span>{tab.label}</span>
              <span className="flex items-center gap-1.5">
                <span className="w-1 h-1 rounded-full bg-teal animate-pulse" />
                Visualizer
              </span>
            </div>
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
    const nodes = [
      { x: 80, y: 80, l: "DAMAN", code: "DM" },
      { x: 320, y: 80, l: "THIQA", code: "TH" },
      { x: 40, y: 200, l: "NAS", code: "NA" },
      { x: 360, y: 200, l: "MEDNET", code: "MN" },
      { x: 110, y: 340, l: "NEXtCARE", code: "NX" },
      { x: 290, y: 340, l: "ADNIC", code: "AD" },
    ];
    return (
      <div className="absolute inset-0 grid place-items-center">
        <svg viewBox="0 0 400 400" className="w-[88%] h-[88%]" fill="none">
          <defs>
            <radialGradient id="center-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.7" />
              <stop offset="60%" stopColor="#0E5E5E" stopOpacity="0.12" />
              <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="node-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* concentric pulse rings */}
          {[60, 90, 120].map((r, i) => (
            <motion.circle
              key={r}
              cx="200"
              cy="200"
              r={r}
              stroke="rgba(14,94,94,0.18)"
              strokeWidth="0.8"
              strokeDasharray="2 4"
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: [0, 0.7, 0.4], scale: [0.85, 1.04, 1] }}
              transition={{
                duration: 3.2,
                delay: 0.3 + i * 0.3,
                repeat: Infinity,
                repeatDelay: 1.2,
                ease: "easeOut",
              }}
            />
          ))}

          {/* center glow */}
          <circle cx="200" cy="200" r="90" fill="url(#center-glow)" />

          {/* lines from outer to center */}
          {nodes.map((n, i) => (
            <motion.line
              key={`line-${n.l}`}
              x1="200"
              y1="200"
              x2={n.x}
              y2={n.y}
              stroke="rgba(14,94,94,0.45)"
              strokeWidth="0.8"
              strokeDasharray="2 3"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ delay: 0.3 + i * 0.06, duration: 0.7 }}
            />
          ))}

          {/* traveling data packets on each line */}
          {nodes.map((n, i) => {
            const dx = 200 - n.x;
            const dy = 200 - n.y;
            return (
              <motion.circle
                key={`packet-${n.l}`}
                cx={n.x}
                cy={n.y}
                r="2.5"
                fill="#0E5E5E"
                initial={{ opacity: 0 }}
                animate={{
                  opacity: [0, 1, 1, 0],
                  cx: [n.x, n.x + dx],
                  cy: [n.y, n.y + dy],
                }}
                transition={{
                  duration: 2.2,
                  delay: 1.4 + i * 0.32,
                  repeat: Infinity,
                  repeatDelay: 1.6,
                  ease: "easeInOut",
                  times: [0, 0.1, 0.9, 1],
                }}
              />
            );
          })}

          {/* outer nodes */}
          {nodes.map((n, i) => (
            <g key={`node-${n.l}`}>
              {/* glow */}
              <motion.circle
                cx={n.x}
                cy={n.y}
                r="34"
                fill="url(#node-glow)"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0.35, 0.6, 0.35] }}
                transition={{
                  duration: 3.6,
                  delay: 0.8 + i * 0.18,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
              {/* outer ring */}
              <motion.circle
                cx={n.x}
                cy={n.y}
                r="18"
                fill="#0A0A0A"
                stroke="rgba(248,246,241,0.22)"
                strokeWidth="0.8"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.45 + i * 0.07, type: "spring", stiffness: 220, damping: 16 }}
              />
              {/* tick marks at cardinals */}
              <g stroke="rgba(248,246,241,0.30)" strokeWidth="0.8">
                <line x1={n.x} y1={n.y - 19.5} x2={n.x} y2={n.y - 16.5} />
                <line x1={n.x} y1={n.y + 16.5} x2={n.x} y2={n.y + 19.5} />
                <line x1={n.x - 19.5} y1={n.y} x2={n.x - 16.5} y2={n.y} />
                <line x1={n.x + 16.5} y1={n.y} x2={n.x + 19.5} y2={n.y} />
              </g>
              {/* code in node */}
              <motion.text
                x={n.x}
                y={n.y + 3.5}
                textAnchor="middle"
                fontSize="9"
                fontWeight="600"
                fill="rgba(248,246,241,0.85)"
                fontFamily="ui-sans-serif, system-ui, sans-serif"
                letterSpacing="0.5"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 + i * 0.07 }}
              >
                {n.code}
              </motion.text>
              {/* label below */}
              <motion.text
                x={n.x}
                y={n.y + 38}
                textAnchor="middle"
                fontSize="8.5"
                fill="rgba(248,246,241,0.55)"
                fontFamily="ui-sans-serif, system-ui, sans-serif"
                letterSpacing="2"
                initial={{ opacity: 0, y: n.y + 44 }}
                animate={{ opacity: 1, y: n.y + 38 }}
                transition={{ delay: 0.8 + i * 0.07, duration: 0.4 }}
              >
                {n.l}
              </motion.text>
            </g>
          ))}

          {/* center node */}
          <motion.circle
            cx="200"
            cy="200"
            r="38"
            fill="#0A0A0A"
            stroke="#0E5E5E"
            strokeWidth="1.2"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.6, delay: 0.1, type: "spring", stiffness: 200, damping: 18 }}
          />
          <motion.circle
            cx="200"
            cy="200"
            r="42"
            stroke="#0E5E5E"
            strokeOpacity="0.6"
            strokeWidth="0.6"
            fill="none"
            animate={{ r: [42, 50, 42], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 2.8, repeat: Infinity, ease: "easeOut" }}
          />
          <text
            x="200"
            y="197"
            textAnchor="middle"
            fontSize="9.5"
            fontWeight="600"
            fill="#F8F6F1"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="2.2"
          >
            SOLVERE
          </text>
          <line x1="184" y1="204" x2="216" y2="204" stroke="rgba(14,94,94,0.6)" strokeWidth="0.6" />
          <text
            x="200"
            y="215"
            textAnchor="middle"
            fontSize="6.5"
            fill="rgba(248,246,241,0.55)"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="2"
          >
            CORE
          </text>

          {/* corner instrument labels */}
          <g fontFamily="ui-sans-serif, system-ui, sans-serif" fill="rgba(248,246,241,0.35)" fontSize="7" letterSpacing="1.8">
            <text x="16" y="22">PAYER MESH</text>
            <text x="384" y="22" textAnchor="end">24 PORTALS</text>
            <text x="16" y="390">LATENCY · LIVE</text>
            <text x="384" y="390" textAnchor="end">eCLAIMLINK</text>
          </g>
          {/* corner brackets */}
          {[
            { x: 10, y: 28, rot: 0 },
            { x: 390, y: 28, rot: 90 },
            { x: 390, y: 376, rot: 180 },
            { x: 10, y: 376, rot: 270 },
          ].map((c, i) => (
            <g key={i} transform={`translate(${c.x} ${c.y}) rotate(${c.rot})`} stroke="rgba(248,246,241,0.25)" strokeWidth="0.8" fill="none">
              <path d="M 0 0 L 0 -10 L 10 -10" />
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
