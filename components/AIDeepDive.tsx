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
  const [inView, setInView] = useState(false);
  const sectionRef = useRef<HTMLElement | null>(null);
  const tab = tabs[active];

  // reset to Triage every time the section enters view, so every visitor sees it first
  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          setActive(0);
          setCycleKey((k) => k + 1);
        } else {
          setInView(false);
        }
      },
      { threshold: 0.35 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // auto-cycle only while in view
  useEffect(() => {
    if (!inView) return;
    const id = setTimeout(() => {
      setActive((a) => (a + 1) % tabs.length);
      setCycleKey((k) => k + 1);
    }, AUTO_MS);
    return () => clearTimeout(id);
  }, [active, cycleKey, inView]);

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

            <div className="flex flex-wrap gap-2 sm:gap-2.5 mt-8 mb-8">
              {tabs.map((t, i) => (
                <button
                  key={t.no}
                  onClick={() => go(i)}
                  aria-pressed={active === i}
                  className={`relative overflow-hidden rounded-full px-4 sm:px-5 py-2.5 text-[12.5px] sm:text-[13px] tracking-[0.14em] uppercase border font-medium transition-colors ${
                    active === i
                      ? "bg-teal/[0.10] border-teal/55 text-cream"
                      : "bg-white/[0.03] border-white/[0.18] text-cream/80 hover:bg-white/[0.06] hover:border-white/30 hover:text-cream"
                  }`}
                >
                  {active === i && (
                    <motion.span
                      key={`progress-${cycleKey}`}
                      aria-hidden
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ duration: AUTO_MS / 1000, ease: "linear" }}
                      className="absolute inset-y-0 left-0 right-0 bg-teal/[0.28] origin-left"
                    />
                  )}
                  <span className="relative inline-flex items-baseline gap-2.5 tabular-nums">
                    <span className={active === i ? "text-teal" : "text-teal/80"}>
                      {t.no}
                    </span>
                    <span>{t.key}</span>
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

          {/* RIGHT — mobile: square panel so the 1:1 SVG fills edge-to-edge; desktop: fills column height */}
          <div className="lg:col-span-6 relative aspect-square lg:aspect-auto lg:min-h-0 rounded-3xl border border-white/8 bg-ink-soft/40 backdrop-blur overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={tab.illustration}
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                className="absolute inset-0"
              >
                <Illustration kind={tab.illustration} live={inView} />
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
  live,
}: {
  kind: "triage" | "verify" | "mesh" | "learning";
  live: boolean;
}) {
  if (kind === "triage") return <TriageScene live={live} />;
  if (kind === "verify") return <VerifyScene />;
  if (kind === "mesh") return <MeshScene live={live} />;
  return <LearningScene />;
}

// shared chrome (brackets at corners + corner labels) — brackets sit OUTSIDE label baseline so they never touch glyphs
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
    <g pointerEvents="none">
      {/* corner labels only — brackets removed */}
      <g
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fill="rgba(248,246,241,0.35)"
        fontSize="7"
        letterSpacing="1.6"
      >
        <text x="16" y="18">
          {tl}
        </text>
        <text x="384" y="18" textAnchor="end">
          {tr}
        </text>
        <text x="16" y="394">
          {bl}
        </text>
        <text x="384" y="394" textAnchor="end">
          {br}
        </text>
      </g>
    </g>
  );
}

function TriageScene({ live }: { live: boolean }) {
  // AI triage console: denied claims streamed in, each scored for recoverability against a threshold.
  const rows = [
    { code: "DM", reason: "Eligibility lapse", score: 84 },
    { code: "TH", reason: "Code specificity", score: 91 },
    { code: "NA", reason: "Bundling rule", score: 32 },
    { code: "MN", reason: "Prior auth", score: 73 },
    { code: "NX", reason: "Documentation", score: 26 },
    { code: "AD", reason: "Filing window", score: 88 },
  ];
  // Centered geometry: content sits in x[60..340], width 280, centered on 200.
  // 6 rows + headers + aggregate fills y[78..314], centered vertically with bottom-corner margin.
  const THRESH = 50;
  const labelX = 60;       // left edge of content
  const reasonX = 92;      // after payer chip
  const trackX = 180;      // score bar start
  const trackW = 120;      // score bar width — ends at 300
  const scoreEndX = 320;   // numeric score — right edge anchor
  const verdictX = 334;    // verdict dot
  const aggX = 60;         // aggregate bar left
  const aggW = 280;        // aggregate bar width — ends at 340
  const rowTop = 104;
  const rowStep = 28;
  const rowH = 22;
  const threshX = trackX + (trackW * THRESH) / 100;

  return (
    <div className="absolute inset-0 grid place-items-center">
      <svg viewBox="0 0 400 400" className="w-[96%] h-[96%]" fill="none">
        <defs>
          <linearGradient id="score-fill" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="1" />
          </linearGradient>
          <linearGradient id="agg-fill" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="1" />
          </linearGradient>
        </defs>

        {/* column headers */}
        <text x={labelX} y="86" fontSize="6.5" fill="rgba(248,246,241,0.42)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.6">
          DENIED CLAIM
        </text>
        <text x={trackX} y="86" fontSize="6.5" fill="rgba(248,246,241,0.42)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.6">
          RECOVERABILITY SCORE
        </text>

        {/* threshold guide line spanning the rows */}
        <line
          x1={threshX}
          y1={rowTop - 4}
          x2={threshX}
          y2={rowTop + rows.length * rowStep - 6}
          stroke="rgba(248,246,241,0.18)"
          strokeWidth="0.7"
          strokeDasharray="2 3"
        />
        <text x={threshX} y={rowTop - 8} textAnchor="middle" fontSize="5.5" fill="rgba(248,246,241,0.42)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1">
          THRESHOLD
        </text>

        {/* sweeping scan highlight — only animates when section is visible (saves CPU) */}
        {live && (
          <motion.rect
            x={labelX - 6}
            width={(verdictX + 8) - (labelX - 6)}
            height={rowH}
            rx="4"
            fill="rgba(14,94,94,0.10)"
            initial={{ y: rowTop }}
            animate={{ y: rows.map((_, i) => rowTop + i * rowStep) }}
            transition={{
              duration: 3.6,
              times: rows.map((_, i) => i / (rows.length - 1)),
              repeat: Infinity,
              repeatType: "reverse",
              ease: "easeInOut",
              delay: 1.2,
            }}
          />
        )}

        {/* claim rows */}
        {rows.map((r, i) => {
          const cy = rowTop + i * rowStep + rowH / 2;
          const recoverable = r.score >= THRESH;
          const fillW = (trackW * r.score) / 100;
          return (
            <motion.g
              key={r.code}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 + i * 0.12, ease: [0.22, 1, 0.36, 1] }}
            >
              {/* payer chip */}
              <rect x={labelX} y={cy - 8} width="24" height="16" rx="3" fill="rgba(255,255,255,0.05)" stroke="rgba(248,246,241,0.16)" strokeWidth="0.6" />
              <text x={labelX + 12} y={cy + 2.6} textAnchor="middle" fontSize="7.5" fontWeight="600" fill="rgba(248,246,241,0.82)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="0.4">
                {r.code}
              </text>
              {/* reason */}
              <text x={reasonX} y={cy + 2.6} fontSize="7.5" fill="rgba(248,246,241,0.62)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="0.3">
                {r.reason}
              </text>
              {/* score track */}
              <rect x={trackX} y={cy - 2.5} width={trackW} height="5" rx="2.5" fill="rgba(248,246,241,0.07)" />
              <motion.rect
                x={trackX}
                y={cy - 2.5}
                height="5"
                rx="2.5"
                fill={recoverable ? "url(#score-fill)" : "rgba(248,246,241,0.20)"}
                initial={{ width: 0 }}
                animate={{ width: fillW }}
                transition={{ duration: 0.9, delay: 0.5 + i * 0.12, ease: [0.22, 1, 0.36, 1] }}
              />
              {/* score value — right-anchored so the digit edge sits at scoreEndX, never collides with verdict */}
              <text x={scoreEndX} y={cy + 2.6} textAnchor="end" fontSize="8" fontWeight="500" fill={recoverable ? "#0E5E5E" : "rgba(248,246,241,0.4)"} fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="0.3">
                {r.score}
              </text>
              {/* verdict dot */}
              <motion.circle
                cx={verdictX}
                cy={cy}
                r="3.6"
                fill={recoverable ? "#0E5E5E" : "none"}
                stroke={recoverable ? "none" : "rgba(248,246,241,0.3)"}
                strokeWidth="0.8"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 1.0 + i * 0.12, type: "spring", stiffness: 300, damping: 14 }}
              />
            </motion.g>
          );
        })}

        {/* aggregate split bar */}
        {(() => {
          const aggY = rowTop + rows.length * rowStep + 22;
          const recW = aggW * 0.68;
          return (
            <g>
              <text x={aggX} y={aggY - 9} fontSize="6.5" fill="rgba(248,246,241,0.42)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.6">
                247 CLAIMS · SCORED
              </text>
              <rect x={aggX} y={aggY} width={aggW} height="10" rx="5" fill="rgba(248,246,241,0.08)" />
              <motion.rect
                x={aggX}
                y={aggY}
                height="10"
                rx="5"
                fill="url(#agg-fill)"
                initial={{ width: 0 }}
                animate={{ width: recW }}
                transition={{ duration: 1.1, delay: 1.4, ease: [0.22, 1, 0.36, 1] }}
              />
              <text x={aggX} y={aggY + 26} fontSize="7" fill="#0E5E5E" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.2">
                ● RECOVERABLE · 68%
              </text>
              <text x={aggX + aggW} y={aggY + 26} textAnchor="end" fontSize="7" fill="rgba(248,246,241,0.45)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.2">
                WRITE-OFF · 32%
              </text>
            </g>
          );
        })()}

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
  // Doc itself centered on viewBox midpoint (200) — what the eye reads as "centered".
  // docW=300 → docX=50, docR=350. Seal at (346, 310), right edge ~391 (inside 400).
  const docX = 50;
  const docY = 48;
  const docW = 300;
  const docH = 310;
  const docR = docX + docW; // 350
  const innerX = docX + 20; // 70
  const innerR = docR - 20; // 330
  const lines = [
    { w: 230, y: docY + 68 },
    { w: 198, y: docY + 88 },
    { w: 244, y: docY + 108 },
    { w: 162, y: docY + 128 },
  ];
  const checks = ["ELIG", "CODE", "DOCS", "MOD"];

  return (
    <div className="absolute inset-0 grid place-items-center">
      <svg viewBox="0 0 400 400" className="w-[98%] h-[98%]" fill="none">
        <defs>
          <radialGradient id="seal-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* document */}
        <motion.rect
          x={docX}
          y={docY}
          width={docW}
          height={docH}
          rx="10"
          fill="rgba(255,255,255,0.025)"
          stroke="rgba(248,246,241,0.18)"
          strokeWidth="0.9"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
        />

        {/* header (relative to docY=56) */}
        <text x={innerX} y={docY + 26} fontSize="7.5" fill="rgba(248,246,241,0.55)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.6">
          CLAIM · DM-24698
        </text>
        <text x={innerR} y={docY + 26} textAnchor="end" fontSize="7.5" fill="rgba(248,246,241,0.55)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.6">
          AED 22,500
        </text>
        <line x1={innerX} y1={docY + 38} x2={innerR} y2={docY + 38} stroke="rgba(248,246,241,0.12)" />

        {/* body lines */}
        {lines.map((l, i) => (
          <motion.rect
            key={i}
            x={innerX}
            y={l.y}
            width={l.w}
            height="4.5"
            rx="2.25"
            fill="rgba(248,246,241,0.15)"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            style={{ transformOrigin: `${innerX}px ${l.y}px` }}
            transition={{ duration: 0.5, delay: 0.2 + i * 0.07 }}
          />
        ))}

        {/* verification checks */}
        <text x={innerX} y={docY + 168} fontSize="7.5" fill="rgba(248,246,241,0.45)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.8">
          VERIFICATION CHECKS
        </text>
        {checks.map((s, i) => {
          const cw = 60;
          const step = 66;
          const x = innerX + i * step;
          const rectY = docY + 180;
          return (
            <g key={s}>
              <motion.rect
                x={x}
                y={rectY}
                width={cw}
                height="24"
                rx="4"
                stroke="rgba(14,94,94,0.45)"
                strokeWidth="0.8"
                fill="rgba(14,94,94,0.10)"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 + i * 0.1 }}
              />
              <motion.text
                x={x + cw / 2 - 4}
                y={rectY + 15}
                textAnchor="middle"
                fontSize="7.5"
                fill="rgba(248,246,241,0.78)"
                fontFamily="ui-sans-serif, system-ui, sans-serif"
                letterSpacing="0.8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 + i * 0.1 }}
              >
                {s}
              </motion.text>
              <motion.circle
                cx={x + cw - 9}
                cy={rectY + 5}
                r="2.6"
                fill="#0E5E5E"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 1.1 + i * 0.14, type: "spring", stiffness: 280, damping: 13 }}
              />
            </g>
          );
        })}

        {/* signature block */}
        <line x1={innerX} y1={docY + 234} x2={innerR} y2={docY + 234} stroke="rgba(248,246,241,0.12)" />
        <text x={innerX} y={docY + 252} fontSize="7.5" fill="rgba(248,246,241,0.45)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.8">
          REVIEWED BY
        </text>
        <motion.path
          d={`M${innerX} ${docY + 276} c 8 -14 18 -14 28 -2 c 10 11 20 5 30 -6 c 10 -9 22 -2 32 8 c 8 7 18 -3 26 -10`}
          stroke="#F8F6F1"
          strokeOpacity="0.85"
          strokeWidth="1.5"
          strokeLinecap="round"
          fill="none"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ delay: 1.3, duration: 1.3 }}
        />
        <text x={innerX} y={docY + 295} fontSize="7" fill="rgba(248,246,241,0.52)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1">
          M. AL-MARZOUQI · DHA-MC-04812
        </text>

        {/* APPROVED seal stamped on the document's bottom-right corner */}
        <g transform={`translate(${docR - 4} ${docY + 262}) rotate(-8)`}>
          <motion.g
            initial={{ opacity: 0, scale: 0.4 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.7, type: "spring", stiffness: 220, damping: 15 }}
          >
            <circle cx="0" cy="0" r="54" fill="url(#seal-glow)" />
            <circle cx="0" cy="0" r="38" fill="#0A0A0A" stroke="#0E5E5E" strokeWidth="1.5" />
            <circle cx="0" cy="0" r="45" fill="none" stroke="#0E5E5E" strokeOpacity="0.4" strokeWidth="0.7" strokeDasharray="2 3" />
            <text x="0" y="-6" textAnchor="middle" fontSize="8.5" fontWeight="600" fill="#0E5E5E" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.6">
              VERIFIED
            </text>
            <line x1="-17" y1="1" x2="17" y2="1" stroke="rgba(14,94,94,0.5)" strokeWidth="0.7" />
            <text x="0" y="13" textAnchor="middle" fontSize="7" fill="rgba(248,246,241,0.7)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.5">
              DHA · CPC
            </text>
          </motion.g>
        </g>

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

function MeshScene({ live }: { live: boolean }) {
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
      <svg viewBox="0 0 400 400" className="w-[96%] h-[96%]" fill="none">
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
            initial={{ opacity: 0.4, scale: 1 }}
            animate={
              live
                ? { opacity: [0, 0.7, 0.4], scale: [0.85, 1.04, 1] }
                : { opacity: 0.4, scale: 1 }
            }
            transition={
              live
                ? { duration: 3.2, delay: 0.3 + i * 0.3, repeat: Infinity, repeatDelay: 1.2, ease: "easeOut" }
                : { duration: 0 }
            }
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

        {live && nodes.map((n, i) => {
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
              initial={{ opacity: 0.5 }}
              animate={live ? { opacity: [0.35, 0.6, 0.35] } : { opacity: 0.5 }}
              transition={
                live
                  ? { duration: 3.6, delay: 0.8 + i * 0.18, repeat: Infinity, ease: "easeInOut" }
                  : { duration: 0 }
              }
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
        {live && (
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
        )}
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
  // bars shifted down so they live entirely below the annotation row at the top
  const bars = [42, 64, 78, 100, 122, 152, 180, 206];
  const baseY = 340;
  const barW = 22;
  const colStep = 36;
  const xStart = 70;
  return (
    <div className="absolute inset-0 grid place-items-center">
      <svg viewBox="0 0 400 400" className="w-[96%] h-[96%]" fill="none">
        <defs>
          <linearGradient id="bar-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0.18" />
          </linearGradient>
        </defs>

        {/* annotation badge — STATIC transform (no Framer x/y clobber), opacity-only animation */}
        <g transform="translate(58 52)">
          <motion.g
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <rect x="0" y="0" width="150" height="44" rx="8" fill="rgba(14,94,94,0.10)" stroke="rgba(14,94,94,0.35)" />
            <text x="14" y="17" fontSize="6" fill="rgba(248,246,241,0.55)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.5">
              RULE LIBRARY · GROWTH
            </text>
            <text x="14" y="34" fontSize="13" fontWeight="600" fill="#0E5E5E" fontFamily="ui-sans-serif, system-ui, sans-serif">
              +312 / month
            </text>
          </motion.g>
        </g>

        {/* multiplier pill — STATIC transform, top-right, clear of badge & corner labels */}
        <g transform="translate(252 60)">
          <motion.g
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.45, duration: 0.5 }}
          >
            <rect x="0" y="0" width="90" height="26" rx="13" fill="rgba(14,94,94,0.08)" stroke="rgba(14,94,94,0.30)" />
            <circle cx="14" cy="13" r="2" fill="#0E5E5E" />
            <text x="23" y="16" fontSize="7" fill="rgba(248,246,241,0.78)" fontFamily="ui-sans-serif, system-ui, sans-serif" letterSpacing="1.2">
              4.1× IN 8Q
            </text>
          </motion.g>
        </g>

        {/* y axis gridlines — sit below annotations */}
        {[140, 180, 220, 260, 300].map((y, i) => (
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
              fontSize="6"
              fill="rgba(248,246,241,0.40)"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
              letterSpacing="1"
            >
              {[100, 80, 60, 40, 20][i]}
            </text>
          </g>
        ))}

        {/* baseline */}
        <line x1="60" y1={baseY} x2="360" y2={baseY} stroke="rgba(248,246,241,0.22)" />

        {/* x axis tick labels */}
        {["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"].map((q, i) => (
          <text
            key={q}
            x={xStart + i * colStep + barW / 2}
            y={baseY + 16}
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
            x={xStart + i * colStep}
            y={baseY - h}
            width={barW}
            height={h}
            rx="2"
            fill={i === bars.length - 1 ? "#0E5E5E" : "url(#bar-grad)"}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{
              duration: 0.7,
              delay: 0.6 + i * 0.08,
              ease: [0.22, 1, 0.36, 1],
            }}
            style={{ transformOrigin: `${xStart + i * colStep + barW / 2}px ${baseY}px` }}
          />
        ))}

        {/* bar value labels */}
        {bars.map((h, i) => (
          <motion.text
            key={i}
            x={xStart + i * colStep + barW / 2}
            y={baseY - h - 6}
            textAnchor="middle"
            fontSize="6.5"
            fontWeight="500"
            fill={i === bars.length - 1 ? "#0E5E5E" : "rgba(248,246,241,0.55)"}
            fontFamily="ui-sans-serif, system-ui, sans-serif"
            letterSpacing="0.3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.3 + i * 0.08 }}
          >
            {Math.round((h / 220) * 100)}
          </motion.text>
        ))}

        {/* trend curve over bar tops */}
        <motion.path
          d={`M${xStart + barW / 2},${baseY - bars[0]} ${bars
            .map(
              (h, i) =>
                `L${xStart + i * colStep + barW / 2},${baseY - h}`
            )
            .join(" ")}`}
          stroke="rgba(14,94,94,0.65)"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeDasharray="4 4"
          fill="none"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.4, delay: 1.4 }}
        />

        {/* end marker glow */}
        <motion.circle
          cx={xStart + (bars.length - 1) * colStep + barW / 2}
          cy={baseY - bars[bars.length - 1]}
          r="6"
          fill="rgba(14,94,94,0.25)"
          stroke="#0E5E5E"
          strokeWidth="1"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            delay: 2.6,
            type: "spring",
            stiffness: 240,
            damping: 14,
          }}
        />

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
