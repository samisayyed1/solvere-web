"use client";

import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useRef, useState } from "react";

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
      className="relative pt-28 md:pt-36 pb-20 md:pb-24 overflow-hidden"
    >
      <AmbientBackdrop />

      <div className="relative mx-auto max-w-container px-6 lg:px-10 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-stretch">
        <div className="lg:col-span-7 flex flex-col">
          <motion.div
            variants={fade}
            custom={0}
            initial="hidden"
            animate="show"
            className="eyebrow inline-flex items-center gap-2 mb-7"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-60 animate-ping" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-teal" />
            </span>
            ABU DHABI · UNITED ARAB EMIRATES
          </motion.div>

          <motion.h1
            variants={fade}
            custom={1}
            initial="hidden"
            animate="show"
            className="h-display text-[40px] leading-[1.02] sm:text-[52px] md:text-[64px] lg:text-[72px] text-ink"
          >
            A new standard
            <br />
            for{" "}
            <span className="text-teal">UAE claim recovery.</span>
          </motion.h1>

          <motion.p
            variants={fade}
            custom={2}
            initial="hidden"
            animate="show"
            className="mt-7 max-w-[56ch] text-[17px] md:text-[18px] leading-[1.6] text-muted"
          >
            Solvere uses AI agents and a DHA-licensed medical coder to recover
            the denied insurance claims your billers gave up on — end to end,
            every payer, pay only on recovery.
          </motion.p>

          <motion.div
            variants={fade}
            custom={3}
            initial="hidden"
            animate="show"
            className="mt-9 flex flex-col sm:flex-row gap-3 sm:items-center"
          >
            <a
              href="#final-cta"
              className="group inline-flex items-center justify-between gap-3 rounded-full bg-ink text-cream pl-6 pr-2 py-2.5 text-[15px] font-medium hover:bg-teal-deep transition-colors"
            >
              Book a 20-minute audit call
              <span className="grid place-items-center w-9 h-9 rounded-full bg-cream text-ink transition-transform group-hover:translate-x-0.5">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                  <path d="M1 6.5h11M7 2.5l4.5 4-4.5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
                </svg>
              </span>
            </a>
            <a
              href="#dashboard"
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
            className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] uppercase tracking-[0.18em] text-muted"
          >
            <Pill>No software</Pill>
            <Pill>No integration</Pill>
            <Pill>Pay only on recovery</Pill>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="lg:col-span-5 w-full max-w-[520px] lg:max-w-none justify-self-start lg:justify-self-end flex"
        >
          <LiveRecoveryCard />
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

function AmbientBackdrop() {
  return (
    <>
      <div
        aria-hidden
        className="absolute -top-40 -left-40 w-[760px] h-[760px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(14,94,94,0.10), rgba(14,94,94,0) 70%)",
        }}
      />
      <div
        aria-hidden
        className="absolute top-32 -right-20 w-[560px] h-[560px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(closest-side, rgba(180,83,9,0.05), rgba(180,83,9,0) 70%)",
        }}
      />
      {/* desktop only — animated dot grid is expensive on mobile GPUs */}
      <motion.div
        aria-hidden
        animate={{ backgroundPosition: ["0px 0px", "32px 32px"] }}
        transition={{ duration: 26, repeat: Infinity, ease: "linear" }}
        className="hidden md:block absolute inset-0 pointer-events-none opacity-[0.32]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(10,10,10,0.10) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
          maskImage:
            "radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 75%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 75%)",
        }}
      />
      {/* mobile fallback — static dot grid, zero animation cost */}
      <div
        aria-hidden
        className="md:hidden absolute inset-0 pointer-events-none opacity-[0.22]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(10,10,10,0.10) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
          maskImage:
            "radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 75%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 75%)",
        }}
      />
    </>
  );
}

function LiveRecoveryCard() {
  const target = 2_340_891;
  const value = useMotionValue(0);
  const rounded = useTransform(value, (v) =>
    Math.round(v).toLocaleString("en-AE")
  );
  const [display, setDisplay] = useState("0");
  const cardRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(true); // assume in view on first paint

  useEffect(() => {
    const controls = animate(value, target, {
      duration: 2.6,
      delay: 0.6,
      ease: [0.22, 1, 0.36, 1],
    });
    const unsub = rounded.on("change", (v) => setDisplay(v));
    return () => {
      controls.stop();
      unsub();
    };
  }, [rounded, value]);

  // pause the recurring counter-bump when scrolled out of view (mobile CPU saver)
  useEffect(() => {
    const el = cardRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => setInView(entry.isIntersecting),
      { threshold: 0.1 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!inView) return;
    const i = setInterval(() => {
      const bump = Math.floor(800 + Math.random() * 3200);
      const current = value.get();
      animate(value, current + bump, { duration: 1.4, ease: "easeOut" });
    }, 4200);
    return () => clearInterval(i);
  }, [value, inView]);

  const ticks = [
    { payer: "Daman", amount: "AED 22,500", t: "2m" },
    { payer: "Thiqa", amount: "AED 11,200", t: "8m" },
    { payer: "MedNet", amount: "AED 9,300", t: "14m" },
    { payer: "NEXtCARE", amount: "AED 6,100", t: "21m" },
  ];

  const stats = [
    { label: "Claims paid", value: "1,284" },
    { label: "Win rate", value: "62%" },
    { label: "Avg cycle", value: "11d" },
  ];

  // 14-day spark — climbing trend
  const spark = [18, 22, 19, 28, 31, 27, 35, 38, 33, 44, 49, 47, 56, 62];

  return (
    <div ref={cardRef} className="relative rounded-2xl border border-rule bg-cream-deep/95 md:bg-cream-deep/80 md:backdrop-blur p-6 md:p-7 shadow-[0_30px_80px_-40px_rgba(10,10,10,0.30)] flex flex-col w-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2 text-[10px] tracking-[0.22em] uppercase text-muted">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-70 animate-ping" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal" />
          </span>
          Recovered · last 30 days
        </div>
      </div>

      <div className="flex items-baseline gap-3">
        <span className="text-[12px] tracking-[0.22em] uppercase text-muted">
          AED
        </span>
        <span className="h-display text-[40px] sm:text-[44px] md:text-[50px] text-ink tabular-nums leading-none tracking-[-0.035em]">
          {display}
        </span>
      </div>

      <div className="mt-5">
        <Sparkline data={spark} />
        <div className="mt-3 flex items-center justify-between text-[10px] tracking-[0.18em] uppercase text-muted">
          <span>14-day recovery trend</span>
          <span className="inline-flex items-center gap-1.5 text-teal">
            <Arrow /> +28%
          </span>
        </div>
      </div>

      <div className="mt-6 pt-5 border-t border-rule grid grid-cols-3 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="flex flex-col gap-1.5">
            <span className="text-[10px] tracking-[0.22em] uppercase text-muted">
              {s.label}
            </span>
            <span className="h-display text-[20px] text-ink tabular-nums leading-none">
              {s.value}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-5 border-t border-rule">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[10px] tracking-[0.22em] uppercase text-muted">
            Latest recoveries
          </span>
          <span className="inline-flex items-center gap-1.5 text-[10px] tracking-[0.18em] uppercase text-muted/70">
            <span className="w-1 h-1 rounded-full bg-teal animate-pulse" />
            Live
          </span>
        </div>
        <div className="space-y-2.5">
          {ticks.map((t, i) => (
            <motion.div
              key={t.payer}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.0 + i * 0.18, duration: 0.5 }}
              className="flex items-center justify-between text-[13px] py-1"
            >
              <span className="flex items-center gap-2.5 text-ink-soft">
                <span className="w-1 h-1 rounded-full bg-teal" />
                {t.payer}
              </span>
              <span className="flex items-center gap-3">
                <span className="text-ink tabular-nums font-medium">
                  {t.amount}
                </span>
                <span className="text-[10px] text-muted tabular-nums w-12 text-right">
                  {t.t} ago
                </span>
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="mt-auto pt-5 border-t border-rule flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="grid place-items-center w-7 h-7 rounded-full bg-teal/12 border border-teal/30">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
              <path
                d="M1 5.5l3 3 6-6"
                stroke="#0E5E5E"
                strokeWidth="1.7"
                strokeLinecap="square"
              />
            </svg>
          </span>
          <div className="flex flex-col">
            <span className="text-[11px] text-ink-soft leading-tight">
              Verified by DHA-licensed coder
            </span>
            <span className="text-[10px] tracking-[0.18em] uppercase text-muted leading-tight mt-0.5">
              NDA · DIFC compliant
            </span>
          </div>
        </div>
        <span className="text-[10px] tracking-[0.18em] uppercase text-muted">
          v2.4
        </span>
      </div>
    </div>
  );
}

function Sparkline({ data }: { data: number[] }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const w = 480;
  const h = 64;
  const pad = 4;
  const step = (w - pad * 2) / (data.length - 1);
  const norm = (v: number) =>
    h - pad - ((v - min) / (max - min)) * (h - pad * 2);
  const points = data.map((v, i) => [pad + i * step, norm(v)] as const);
  const linePath = points
    .map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`))
    .join(" ");
  const areaPath = `${linePath} L${w - pad},${h} L${pad},${h} Z`;
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="w-full h-14"
      preserveAspectRatio="none"
      aria-hidden
    >
      <defs>
        <linearGradient id="spark-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0E5E5E" stopOpacity="0.20" />
          <stop offset="100%" stopColor="#0E5E5E" stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.path
        d={areaPath}
        fill="url(#spark-grad)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 1.0 }}
      />
      <motion.path
        d={linePath}
        fill="none"
        stroke="#0E5E5E"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.4, delay: 0.8, ease: [0.22, 1, 0.36, 1] }}
      />
      <motion.circle
        cx={points[points.length - 1][0]}
        cy={points[points.length - 1][1]}
        r="3.5"
        fill="#0E5E5E"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 2.1, type: "spring", stiffness: 280, damping: 14 }}
      />
    </svg>
  );
}

function Arrow() {
  return (
    <svg width="9" height="9" viewBox="0 0 9 9" fill="none">
      <path
        d="M2 7l5-5M3 2h4v4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="square"
      />
    </svg>
  );
}
