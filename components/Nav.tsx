"use client";

import { motion, useScroll, useTransform } from "framer-motion";

export default function Nav() {
  const { scrollY } = useScroll();
  const bg = useTransform(
    scrollY,
    [0, 80],
    ["rgba(248,246,241,0)", "rgba(248,246,241,0.85)"]
  );
  const border = useTransform(
    scrollY,
    [0, 80],
    ["rgba(229,224,214,0)", "rgba(229,224,214,1)"]
  );
  const blur = useTransform(scrollY, [0, 80], ["blur(0px)", "blur(12px)"]);

  return (
    <motion.header
      style={{
        backgroundColor: bg,
        borderBottomColor: border,
        backdropFilter: blur,
        WebkitBackdropFilter: blur,
      }}
      className="fixed top-0 inset-x-0 z-40 border-b"
    >
      <div className="mx-auto max-w-container px-6 lg:px-10 h-16 flex items-center justify-between">
        <a href="#top" className="flex items-center gap-2">
          <span className="h-serif text-[22px] tracking-tightest text-ink">
            Solvere
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-teal" />
        </a>
        <nav className="hidden md:flex items-center gap-8 text-[13px] text-ink-soft/80">
          <a className="hover:text-ink transition-colors" href="#how">How it works</a>
          <a className="hover:text-ink transition-colors" href="#capability">What we do</a>
          <a className="hover:text-ink transition-colors" href="#deep-dive">Under the hood</a>
          <a className="hover:text-ink transition-colors" href="#founding">Founding cohort</a>
        </nav>
        <a
          href="#final-cta"
          className="group inline-flex items-center gap-2 rounded-full bg-ink text-cream pl-5 pr-2 py-1.5 text-[13px] font-medium hover:bg-teal-deep transition-colors"
        >
          Book a call
          <span className="grid place-items-center w-7 h-7 rounded-full bg-cream text-ink transition-transform group-hover:translate-x-0.5">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
              <path
                d="M1 5.5h9M6 1.5l4 4-4 4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
            </svg>
          </span>
        </a>
      </div>
    </motion.header>
  );
}
