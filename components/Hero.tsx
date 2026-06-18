"use client";

import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useState } from "react";

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

      <div className="relative mx-auto max-w-container px-6 lg:px-10 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-start">
        <div className="lg:col-span-7">
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

        {/* live recovery panel */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="lg:col-span-5 w-full max-w-[440px] lg:max-w-none justify-self-start lg:justify-self-end lg:mt-2"
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
      <motion.div
        aria-hidden
        animate={{ backgroundPosition: ["0px 0px", "32px 32px"] }}
        transition={{ duration: 26, repeat: Infinity, ease: "linear" }}
        className="absolute inset-0 pointer-events-none opacity-[0.32]"
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

  useEffect(() => {
    const i = setInterval(() => {
      const bump = Math.floor(800 + Math.random() * 3200);
      const current = value.get();
      animate(value, current + bump, { duration: 1.4, ease: "easeOut" });
    }, 4200);
    return () => clearInterval(i);
  }, [value]);

  const ticks = [
    { payer: "Daman", amount: "AED 22,500", t: "2m" },
    { payer: "Thiqa", amount: "AED 11,200", t: "8m" },
    { payer: "MedNet", amount: "AED 9,300", t: "14m" },
    { payer: "NEXtCARE", amount: "AED 6,100", t: "21m" },
  ];

  return (
    <div className="relative rounded-2xl border border-rule bg-cream-deep/80 backdrop-blur p-6 md:p-7 shadow-[0_30px_80px_-40px_rgba(10,10,10,0.30)]">
      <div className="flex items-center justify-between mb-7">
        <div className="flex items-center gap-2 text-[10px] tracking-[0.22em] uppercase text-muted">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-70 animate-ping" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal" />
          </span>
          Recovered · last 30 days
        </div>
        <span className="text-[10px] tracking-[0.18em] uppercase text-amber">
          Sample
        </span>
      </div>

      <div className="flex items-baseline gap-3">
        <span className="text-[13px] tracking-[0.22em] uppercase text-muted">
          AED
        </span>
        <span className="h-display text-[40px] sm:text-[46px] md:text-[52px] text-ink tabular-nums leading-none tracking-[-0.035em]">
          {display}
        </span>
      </div>

      <div className="mt-7 pt-5 border-t border-rule">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[10px] tracking-[0.22em] uppercase text-muted">
            Latest recoveries
          </span>
          <span className="text-[10px] tracking-[0.18em] uppercase text-muted/70">
            Live
          </span>
        </div>
        <div className="space-y-3">
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
    </div>
  );
}
