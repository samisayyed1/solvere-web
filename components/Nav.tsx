"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { useEffect, useState } from "react";

const links = [
  { href: "#dashboard", label: "Inside Solvere" },
  { href: "#capability", label: "What we do" },
  { href: "#deep-dive", label: "Under the hood" },
  { href: "#founding", label: "Founding cohort" },
];

export default function Nav() {
  const { scrollY } = useScroll();
  const bg = useTransform(
    scrollY,
    [0, 80],
    ["rgba(248,246,241,0.65)", "rgba(248,246,241,0.92)"]
  );
  const border = useTransform(
    scrollY,
    [0, 80],
    ["rgba(229,224,214,0.5)", "rgba(229,224,214,1)"]
  );
  const padding = useTransform(scrollY, [0, 80], ["18px", "10px"]);

  const [active, setActive] = useState<string>("");

  useEffect(() => {
    const sections = links
      .map((l) => document.querySelector(l.href))
      .filter(Boolean) as Element[];
    if (!sections.length) return;
    const obs = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActive("#" + visible.target.id);
      },
      { rootMargin: "-30% 0px -55% 0px", threshold: [0.1, 0.5, 1] }
    );
    sections.forEach((s) => obs.observe(s));
    return () => obs.disconnect();
  }, []);

  return (
    <motion.header
      style={{
        backgroundColor: bg,
        borderBottomColor: border,
      }}
      className="fixed top-0 inset-x-0 z-40 border-b md:[backdrop-filter:blur(14px)] md:[-webkit-backdrop-filter:blur(14px)]"
    >
      <motion.div
        style={{ paddingTop: padding, paddingBottom: padding }}
        className="mx-auto max-w-container px-6 lg:px-10 flex items-center justify-between gap-6"
      >
        {/* wordmark + status */}
        <a href="#top" className="flex items-center gap-3 group">
          <span className="h-serif text-[22px] tracking-[-0.02em] text-ink leading-none">
            Solvere
          </span>
          <span aria-hidden className="hidden sm:block w-px h-4 bg-rule" />
          <span className="hidden sm:flex items-center gap-1.5 text-[10px] tracking-[0.22em] uppercase text-muted">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-60 animate-ping" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal" />
            </span>
            Abu Dhabi
          </span>
        </a>

        {/* center nav */}
        <nav className="hidden md:flex items-center gap-1 absolute left-1/2 -translate-x-1/2">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className={`relative px-3.5 py-1.5 text-[13px] rounded-full transition-colors ${
                active === l.href
                  ? "text-ink"
                  : "text-ink-soft/65 hover:text-ink"
              }`}
            >
              {active === l.href && (
                <motion.span
                  layoutId="nav-active"
                  className="absolute inset-0 rounded-full bg-ink/[0.06]"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <span className="relative">{l.label}</span>
            </a>
          ))}
        </nav>

        {/* right cluster */}
        <div className="flex items-center gap-2">
          <a
            href="mailto:hello@solvere.ai"
            className="hidden lg:inline-flex items-center gap-2 text-[12px] text-muted hover:text-ink transition-colors px-3 py-1.5"
          >
            hello@solvere.ai
          </a>
          <span aria-hidden className="hidden lg:block w-px h-4 bg-rule" />
          <a
            href="#final-cta"
            className="group inline-flex items-center gap-2 rounded-full bg-ink text-cream pl-4 pr-1.5 py-1.5 text-[13px] font-medium hover:bg-teal-deep transition-colors"
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
      </motion.div>
    </motion.header>
  );
}
