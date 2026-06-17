"use client";

// §7.1 — sticky nav. Transparent on cream at top; fades to cream + bottom rule after 80px scroll.
// No links. No menu. Just wordmark + single CTA.

import { useEffect, useState } from "react";
import { BookACallButton } from "@/components/BookACallButton";

export function Nav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      aria-label="Site navigation"
      className={[
        "sticky top-0 z-40 transition-[background-color,border-color] duration-200 ease-out",
        scrolled
          ? "bg-cream border-b border-rule"
          : "bg-transparent border-b border-transparent",
      ].join(" ")}
    >
      <div className="mx-auto flex max-w-content items-center justify-between px-3 md:px-5 h-[56px] md:h-[72px]">
        <a
          href="#main"
          aria-label="Solvere"
          className="font-display font-medium text-[22px] leading-none text-ink"
        >
          Solvere
        </a>
        <BookACallButton
          label="Book a call"
          variant="nav"
          ariaLabel="Book a 20-minute audit call"
        />
      </div>
    </header>
  );
}
