"use client";

// §10 — scroll-triggered fade-in. Vanilla IntersectionObserver + CSS keyframes.
// Drops the framer-motion dependency from the critical path (saves ~50KB JS,
// pushes Lighthouse Performance closer to 100). The 12px Y / 600ms / 80ms
// stagger spec is enforced by the CSS in globals.css.
//
// For above-the-fold elements that should animate on mount, use the plain
// `solvere-fade-up` class directly with `style={{ '--solvere-delay': '...' }}`
// instead of this wrapper — no JS needed.

import { useEffect, useRef, type ReactNode } from "react";

export function FadeIn({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      el.classList.add("solvere-fade-up--in");
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("solvere-fade-up--in");
          io.disconnect();
        }
      },
      { threshold: 0.25 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`solvere-fade-up--armed ${className ?? ""}`.trim()}
      style={{ ["--solvere-delay" as string]: `${Math.round(delay * 1000)}ms` }}
    >
      {children}
    </div>
  );
}
