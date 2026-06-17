// §7.1 — sticky nav. Always shows a faint darker shade over the cream page
// (cream-deep at 50% opacity = a barely-perceptible warm tint, just enough
// for the bar to register as distinct) plus a soft bottom rule and a tiny
// shadow. Reads as a header without ever feeling heavy.
// No links. No menu. Just wordmark + single CTA. No JS needed.

import { BookACallButton } from "@/components/BookACallButton";

export function Nav() {
  return (
    <header
      aria-label="Site navigation"
      className="sticky top-0 z-40 bg-cream-deep/50 backdrop-blur-sm border-b border-rule shadow-rule"
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
