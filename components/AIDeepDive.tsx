"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const AUTO_MS = 6500;

const tabs = [
  {
    no: "01",
    key: "TRIAGE",
    label: "AI reads every denial",
    title: "AI reads every denied claim.",
    body:
      "Classification, reason coding, recoverability scoring across hundreds of claims at once. The work that used to take a biller a week happens in minutes — without missing anything that pays.",
    illustration: "triage" as const,
  },
  {
    no: "02",
    key: "VERIFICATION",
    label: "A licensed coder approves",
    title: "A DHA-licensed coder verifies before submission.",
    body:
      "Every high-value or complex claim is reviewed by a UAE-licensed medical coder before it goes back to the payer. The human gate before the payer gateway. Nothing leaves the building unchecked.",
    illustration: "verify" as const,
  },
  {
    no: "03",
    key: "EXECUTION",
    label: "Every payer's portal",
    title: "End-to-end through every payer portal.",
    body:
      "Resubmission and appeal through eClaimLink, Daman, Thiqa, NEXtCARE, NAS, MedNet, ADNIC, Sukoon and the rest. Documentation, follow-up, escalation — handled to outcome, not just to send.",
    illustration: "mesh" as const,
  },
  {
    no: "04",
    key: "LEARNING",
    label: "Every recovery trains the next",
    title: "The system gets sharper every cycle.",
    body:
      "Each payer response updates the rule library. After ten thousand claims, our denial-reason knowledge becomes the moat: nobody else in the GCC can rebuild it quickly.",
    illustration: "learning" as const,
  },
];

export default function AIDeepDive() {
  const [active, setActive] = useState(0);
  const [cycleKey, setCycleKey] = useState(0);
  const tab = tabs[active];

  useEffect(() => {
    const id = setTimeout(() => {
      setActive((a) => (a + 1) % tabs.length);
      setCycleKey((k) => k + 1);
    }, AUTO_MS);
    return () => clearTimeout(id);
  }, [active, cycleKey]);

  const go = (i: number) => {
    setActive(i);
    setCycleKey((k) => k + 1);
  };

  return (
    <section
      id="deep-dive"
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
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-stretch">
          {/* LEFT */}
          <div className="lg:col-span-6 flex flex-col">
            <div className="eyebrow mb-5 text-teal">Under the hood</div>
            <h2 className="h-display text-[32px] sm:text-[40px] md:text-[48px] lg:text-[52px] text-cream leading-[1.04] mb-5 max-w-[15ch]">
              AI-native recovery,{" "}
              <span className="italic font-normal text-teal">human-verified.</span>
            </h2>
            <p className="text-[15px] md:text-[16px] text-cream/60 leading-[1.6] max-w-[52ch]">
              Pure-AI vendors miss what the rules don't cover. Pure-human shops
              can't scale. Solvere ships both, in the same loop.
            </p>

            <div className="flex flex-wrap gap-2 mt-8 mb-8">
              {tabs.map((t, i) => (
                <button
                  key={t.no}
                  onClick={() => go(i)}
                  className={`relative overflow-hidden rounded-full px-3.5 py-1.5 text-[11px] tracking-[0.18em] uppercase border transition-colors ${
                    active === i
                      ? "bg-teal/15 border-teal/40 text-cream"
                      : "bg-transparent border-white/10 text-cream/55 hover:border-white/25 hover:text-cream"
                  }`}
                >
                  {active === i && (
                    <motion.span
                      key={`progress-${cycleKey}`}
                      aria-hidden
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ duration: AUTO_MS / 1000, ease: "linear" }}
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

            <div className="border-t border-white/10 pt-7 flex-1 flex flex-col">
              <AnimatePresence mode="wait">
                <motion.div
                  key={tab.no}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                  className="flex flex-col"
                >
                  <div className="text-[10px] tracking-[0.22em] uppercase text-cream/40 mb-4 flex items-center gap-3">
                    <span className="text-teal">{tab.no}</span>
                    <span className="w-6 h-px bg-white/15" />
                    <span>{tab.key}</span>
                  </div>
                  <h3 className="h-serif text-[26px] sm:text-[30px] md:text-[34px] text-cream leading-[1.1] mb-4 max-w-[20ch]">
                    {tab.title}
                  </h3>
                  <p className="text-[15px] md:text-[16px] text-cream/65 leading-[1.6] max-w-[52ch]">
                    {tab.body}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>

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
              <span className="text-[11px] tracking-[0.18em] uppercase text-cream/45 tabular-nums">
                {String(active + 1).padStart(2, "0")} /{" "}
                {String(tabs.length).padStart(2, "0")}
              </span>
            </div>
          </div>

          {/* RIGHT */}
          <div className="lg:col-span-6 relative min-h-[520px] lg:min-h-0 rounded-3xl border border-white/8 bg-ink-soft/40 backdrop-blur overflow-hidden">
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
            <div className="absolute top-4 left-5 right-5 flex items-center justify-between text-[10px] tracking-[0.22em] uppercase text-cream/40 pointer-events-none">
              <span className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-teal animate-pulse" />
                Visualizer
              </span>
              <span>{tab.key}</span>
            </div>
            <div className="absolute bottom-4 left-5 right-5 flex items-center justify-between text-[10px] tracking-[0.22em] uppercase text-cream/40 pointer-events-none">
              <span>{tab.label}</span>
              <span className="tabular-nums">
                {String(active + 1).padStart(2, "0")} /{" "}
                {String(tabs.length).padStart(2, "0")}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Illustration({
  kind,
}: {
  kind: "triage" | "verify" | "mesh" | "learning";
}) {
  if (kind === "triage") return <TriageScene />;
  if (kind === "verify") return <VerifyScene />;
  if (kind === "mesh") return <MeshScene />;
  return <LearningScene />;
}

// shared chrome (brackets at corners + corner labels)
function FrameChrome({
  tl,
  tr,
  bl,
  br,
}: {
  tl: string;
  tr: string;
  bl: string;
  br: string;
}) {
  return (
    <g>
      <g
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fill="rgba(248,246,241,0.35)"
        fontSize="7"
        letterSpacing="1.8"
      >
        <text x="16" y="22">
          {tl}
        </text>
        <text x="384" y="22" textAnchor="end">
          {tr}
        </text>
        <text x="16" y="390">
          {bl}
        </text>
        <text x="384" y="390" textAnchor="end">
          {br}
        </text>
      </g>
      {[
        { x: 10, y: 28, rot: 0 },
        { x: 390, y: 28, rot: 90 },
        { x: 390, y: 376, rot: 180 },
        { x: 10, y: 376, rot: 270 },
      ].map((c, i) => (
        <g
          key={i}
          transform={`translate(${c.x} ${c.y}) rotate(${c.rot})`}
          stroke="rgba(248,246,241,0.25)"
          strokeWidth="0.8"
          fill="none"
        >
          <path d="M 0 0 L 0 -10 L 10 -10" />
        </g>
      ))}
    </g>
  );
}

function TriageScene() {
  // funnel of denial dots being scored — recoverable vs not
  const rows = 9;
  const grid: { cx: number; cy: number; r: number; hit: boolean; i: number }[] = [];
  let counter = 0;
  for (let r = 0; r < rows; r++) {
    const cols = rows - r;
    const y = 110 + r * 24;
    const startX = 200 - cols * 14;
    for (let c = 0; c < cols; c++) {
      const cx = startX + c * 28 + 14;
      const hit = ((c + r * 2) % 3) !== 0;
      grid.push({ cx, cy: y, r: 3, hit, i: counter++ });
    }
  }

  return (
    <div className="absolute inset-0 grid place-items-center">
      <svg viewBox="0 0 400 400" className="w-[92%] h-[92%]" fill="none">
        <defs>
          <linearGradient id="triage-fade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0" />
            <stop offset="50%" stopColor="#0E5E5E" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* funnel guides */}
        <motion.path
          d="M110 100 L200 320"
          stroke="rgba(14,94,94,0.35)"
          strokeWidth="0.8"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.2, delay: 0.2 }}
        />
        <motion.path
          d="M290 100 L200 320"
          stroke="rgba(14,94,94,0.35)"
          strokeWidth="0.8"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.2, delay: 0.2 }}
        />

        {/* dots */}
        {grid.map((d) => (
          <motion.circle
            key={d.i}
            cx={d.cx}
            cy={d.cy}
            r={d.r}
            fill={d.hit ? "#0E5E5E" : "rgba(248,246,241,0.18)"}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.4 + d.i * 0.015 }}
          />
        ))}

        {/* scanning sweep */}
        <motion.rect
          x="80"
          y="0"
          width="240"
          height="40"
          fill="url(#triage-fade)"
          initial={{ y: 90 }}
          animate={{ y: [90, 320, 90] }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1.4,
          }}
        />

        {/* outlet — recovered */}
        <motion.g
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6 }}
        >
          <circle cx="200" cy="340" r="14" fill="#0A0A0A" stroke="#0E5E5E" strokeWidth="1.2" />
          <text
            x="200"
            y="343"
            textAnchor="middle"
            fontSize="8"
            fontWeight="600"
            fill="#F8F6F1"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="1"
          >
            68%
          </text>
        </motion.g>

        {/* score column on right */}
        <g transform="translate(330 110)">
          {[0, 1, 2, 3, 4].map((i) => (
            <g key={i}>
              <line
                x1="0"
                y1={i * 24}
                x2="14"
                y2={i * 24}
                stroke="rgba(248,246,241,0.25)"
              />
              <text
                x="20"
                y={i * 24 + 3}
                fontSize="6.5"
                fill="rgba(248,246,241,0.45)"
                fontFamily="ui-sans-serif, system-ui, sans-serif"
                letterSpacing="1"
              >
                {[100, 80, 60, 40, 20][i]}
              </text>
            </g>
          ))}
        </g>

        <FrameChrome
          tl="CLAIMS · 247"
          tr="SCORED · LIVE"
          bl="AI TRIAGE"
          br="RECOVERABLE · 68%"
        />
      </svg>
    </div>
  );
}

function VerifyScene() {
  const lines = [
    { w: 180, y: 110 },
    { w: 220, y: 132 },
    { w: 160, y: 154 },
    { w: 210, y: 176 },
    { w: 140, y: 198 },
    { w: 200, y: 220 },
  ];

  return (
    <div className="absolute inset-0 grid place-items-center">
      <svg viewBox="0 0 400 400" className="w-[88%] h-[88%]" fill="none">
        <defs>
          <radialGradient id="seal-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* document */}
        <motion.rect
          x="80"
          y="80"
          width="240"
          height="260"
          rx="6"
          fill="rgba(255,255,255,0.02)"
          stroke="rgba(248,246,241,0.18)"
          strokeWidth="0.8"
          initial={{ opacity: 0, y: 90 }}
          animate={{ opacity: 1, y: 80 }}
          transition={{ duration: 0.6 }}
        />

        {/* doc header strip */}
        <line x1="80" y1="100" x2="320" y2="100" stroke="rgba(248,246,241,0.10)" />
        <text
          x="92"
          y="94"
          fontSize="6.5"
          fill="rgba(248,246,241,0.45)"
          fontFamily="ui-sans-serif, system-ui, sans-serif"
          letterSpacing="1.5"
        >
          CLAIM · DM-24698
        </text>
        <text
          x="308"
          y="94"
          textAnchor="end"
          fontSize="6.5"
          fill="rgba(248,246,241,0.45)"
          fontFamily="ui-sans-serif, system-ui, sans-serif"
          letterSpacing="1.5"
        >
          AED 22,500
        </text>

        {/* content lines */}
        {lines.map((l, i) => (
          <motion.rect
            key={i}
            x="92"
            y={l.y}
            width={l.w}
            height="4"
            rx="2"
            fill="rgba(248,246,241,0.16)"
            initial={{ scaleX: 0, originX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.5, delay: 0.2 + i * 0.07 }}
          />
        ))}

        {/* stamp row */}
        <g transform="translate(92 250)">
          {["ELIG", "CODE", "DOCS", "MOD", "BUNDLE"].map((s, i) => (
            <g key={s}>
              <motion.rect
                x={i * 44}
                y={0}
                width="36"
                height="18"
                rx="3"
                stroke="rgba(14,94,94,0.45)"
                strokeWidth="0.8"
                fill="rgba(14,94,94,0.10)"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + i * 0.1 }}
              />
              <motion.text
                x={i * 44 + 18}
                y={11}
                textAnchor="middle"
                fontSize="6.5"
                fill="rgba(248,246,241,0.7)"
                fontFamily="ui-sans-serif, system-ui, sans-serif"
                letterSpacing="1"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.95 + i * 0.1 }}
              >
                {s}
              </motion.text>
              <motion.circle
                cx={i * 44 + 30}
                cy={4}
                r="2"
                fill="#0E5E5E"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  delay: 1.2 + i * 0.15,
                  type: "spring",
                  stiffness: 280,
                  damping: 14,
                }}
              />
            </g>
          ))}
        </g>

        {/* coder signature block */}
        <g transform="translate(92 290)">
          <line x1="0" y1="0" x2="216" y2="0" stroke="rgba(248,246,241,0.10)" />
          <text
            x="0"
            y="14"
            fontSize="6.5"
            fill="rgba(248,246,241,0.45)"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="1.5"
          >
            REVIEWED BY
          </text>
          <motion.path
            d="M0 28 q 8 -8 16 0 q 8 -10 18 -4 q 6 6 14 0 q 8 -6 16 2 q 10 6 18 -4 q 6 -4 14 2"
            stroke="#F8F6F1"
            strokeWidth="1.1"
            strokeLinecap="round"
            fill="none"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 1.4, duration: 1.2 }}
          />
          <text
            x="0"
            y="44"
            fontSize="6.5"
            fill="rgba(248,246,241,0.55)"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="1.2"
          >
            M. AL-MARZOUQI · DHA-MC-04812
          </text>
        </g>

        {/* approval seal */}
        <motion.g
          initial={{ opacity: 0, scale: 0.6, rotate: -8 }}
          animate={{ opacity: 1, scale: 1, rotate: -6 }}
          transition={{
            delay: 1.8,
            type: "spring",
            stiffness: 200,
            damping: 16,
          }}
          transform-origin="280 290"
        >
          <circle cx="280" cy="290" r="44" fill="url(#seal-glow)" />
          <circle
            cx="280"
            cy="290"
            r="32"
            fill="#0A0A0A"
            stroke="#0E5E5E"
            strokeWidth="1.4"
          />
          <circle
            cx="280"
            cy="290"
            r="38"
            fill="none"
            stroke="#0E5E5E"
            strokeOpacity="0.4"
            strokeWidth="0.6"
            strokeDasharray="2 3"
          />
          <text
            x="280"
            y="284"
            textAnchor="middle"
            fontSize="6.5"
            fontWeight="600"
            fill="#0E5E5E"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="1.5"
          >
            VERIFIED
          </text>
          <line
            x1="265"
            y1="289"
            x2="295"
            y2="289"
            stroke="rgba(14,94,94,0.4)"
            strokeWidth="0.6"
          />
          <text
            x="280"
            y="299"
            textAnchor="middle"
            fontSize="5.5"
            fill="rgba(248,246,241,0.7)"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="1.5"
          >
            DHA · CPC
          </text>
        </motion.g>

        <FrameChrome
          tl="HUMAN GATE"
          tr="DHA-LICENSED"
          bl="QUEUE · 3"
          br="APPROVED · 24,891"
        />
      </svg>
    </div>
  );
}

function MeshScene() {
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
          <radialGradient id="center-glow-m" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.7" />
            <stop offset="60%" stopColor="#0E5E5E" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="node-glow-m" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
          </radialGradient>
        </defs>

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

        <circle cx="200" cy="200" r="90" fill="url(#center-glow-m)" />

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

        {nodes.map((n, i) => (
          <g key={`node-${n.l}`}>
            <motion.circle
              cx={n.x}
              cy={n.y}
              r="34"
              fill="url(#node-glow-m)"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0.35, 0.6, 0.35] }}
              transition={{
                duration: 3.6,
                delay: 0.8 + i * 0.18,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
            <motion.circle
              cx={n.x}
              cy={n.y}
              r="18"
              fill="#0A0A0A"
              stroke="rgba(248,246,241,0.22)"
              strokeWidth="0.8"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{
                delay: 0.45 + i * 0.07,
                type: "spring",
                stiffness: 220,
                damping: 16,
              }}
            />
            <g stroke="rgba(248,246,241,0.30)" strokeWidth="0.8">
              <line x1={n.x} y1={n.y - 19.5} x2={n.x} y2={n.y - 16.5} />
              <line x1={n.x} y1={n.y + 16.5} x2={n.x} y2={n.y + 19.5} />
              <line x1={n.x - 19.5} y1={n.y} x2={n.x - 16.5} y2={n.y} />
              <line x1={n.x + 16.5} y1={n.y} x2={n.x + 19.5} y2={n.y} />
            </g>
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
            <motion.text
              x={n.x}
              y={n.y + 38}
              textAnchor="middle"
              fontSize="8.5"
              fill="rgba(248,246,241,0.55)"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
              letterSpacing="2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 + i * 0.07, duration: 0.4 }}
            >
              {n.l}
            </motion.text>
          </g>
        ))}

        <motion.circle
          cx="200"
          cy="200"
          r="38"
          fill="#0A0A0A"
          stroke="#0E5E5E"
          strokeWidth="1.2"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            duration: 0.6,
            delay: 0.1,
            type: "spring",
            stiffness: 200,
            damping: 18,
          }}
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
        <line
          x1="184"
          y1="204"
          x2="216"
          y2="204"
          stroke="rgba(14,94,94,0.6)"
          strokeWidth="0.6"
        />
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

        <FrameChrome
          tl="PAYER MESH"
          tr="24 PORTALS"
          bl="LATENCY · LIVE"
          br="eCLAIMLINK"
        />
      </svg>
    </div>
  );
}

function LearningScene() {
  const bars = [50, 78, 92, 118, 142, 178, 210, 240];
  return (
    <div className="absolute inset-0 grid place-items-center">
      <svg viewBox="0 0 400 400" className="w-[90%] h-[90%]" fill="none">
        <defs>
          <linearGradient id="bar-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0.18" />
          </linearGradient>
        </defs>

        {/* y axis gridlines */}
        {[120, 170, 220, 270, 320].map((y, i) => (
          <g key={y}>
            <line
              x1="60"
              y1={y}
              x2="360"
              y2={y}
              stroke="rgba(248,246,241,0.08)"
              strokeDasharray="2 4"
            />
            <text
              x="52"
              y={y + 3}
              textAnchor="end"
              fontSize="6.5"
              fill="rgba(248,246,241,0.40)"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
              letterSpacing="1"
            >
              {[100, 80, 60, 40, 20][i]}
            </text>
          </g>
        ))}

        {/* baseline */}
        <line x1="60" y1="340" x2="360" y2="340" stroke="rgba(248,246,241,0.20)" />

        {/* x axis tick labels */}
        {["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"].map((q, i) => (
          <text
            key={q}
            x={80 + i * 36 + 12}
            y={358}
            textAnchor="middle"
            fontSize="6"
            fill="rgba(248,246,241,0.40)"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="1.2"
          >
            {q}
          </text>
        ))}

        {/* bars */}
        {bars.map((h, i) => (
          <motion.rect
            key={i}
            x={80 + i * 36}
            y={340 - h}
            width="24"
            height={h}
            rx="2"
            fill={i === bars.length - 1 ? "#0E5E5E" : "url(#bar-grad)"}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{
              duration: 0.7,
              delay: 0.2 + i * 0.08,
              ease: [0.22, 1, 0.36, 1],
            }}
            style={{ transformOrigin: `${80 + i * 36 + 12}px 340px` }}
          />
        ))}

        {/* bar value labels */}
        {bars.map((h, i) => (
          <motion.text
            key={i}
            x={80 + i * 36 + 12}
            y={340 - h - 6}
            textAnchor="middle"
            fontSize="7"
            fontWeight="500"
            fill={i === bars.length - 1 ? "#0E5E5E" : "rgba(248,246,241,0.55)"}
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="0.5"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 + i * 0.08 }}
          >
            {Math.round((h / 250) * 100)}
          </motion.text>
        ))}

        {/* trend curve */}
        <motion.path
          d={`M${80 + 0 * 36 + 12},${340 - 50} ${bars
            .map((h, i) => `L${80 + i * 36 + 12},${340 - h}`)
            .join(" ")}`}
          stroke="rgba(14,94,94,0.65)"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeDasharray="4 4"
          fill="none"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.4, delay: 1.1 }}
        />

        {/* end marker glow */}
        <motion.circle
          cx={80 + (bars.length - 1) * 36 + 12}
          cy={340 - bars[bars.length - 1]}
          r="6"
          fill="rgba(14,94,94,0.25)"
          stroke="#0E5E5E"
          strokeWidth="1"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            delay: 2.4,
            type: "spring",
            stiffness: 240,
            damping: 14,
          }}
        />

        {/* annotation badge */}
        <motion.g
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 2.6, duration: 0.5 }}
          transform="translate(220 90)"
        >
          <rect
            x="0"
            y="0"
            width="120"
            height="32"
            rx="4"
            fill="rgba(14,94,94,0.10)"
            stroke="rgba(14,94,94,0.35)"
          />
          <text
            x="10"
            y="13"
            fontSize="6"
            fill="rgba(248,246,241,0.55)"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="1.4"
          >
            RULE LIBRARY
          </text>
          <text
            x="10"
            y="26"
            fontSize="10"
            fontWeight="600"
            fill="#0E5E5E"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="0.5"
          >
            +312 / month
          </text>
        </motion.g>

        <FrameChrome
          tl="LEARNING"
          tr="MODEL v2.4"
          bl="WIN RATE %"
          br="QUARTERS · 8"
        />
      </svg>
    </div>
  );
}
