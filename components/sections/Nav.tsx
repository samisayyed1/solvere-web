// §7.1 — sticky nav. Always shows cream-deep bg + soft bottom rule + tiny
// shadow so it reads as a distinct floating bar over the cream page body
// (per user request: never blends into the page).
// No links. No menu. Just wordmark + single CTA. No JS needed.

import { BookACallButton } from "@/components/BookACallButton";

export function Nav() {
  return (
    <header
      aria-label="Site navigation"
      className="sticky top-0 z-40 bg-cream-deep border-b border-rule shadow-rule"
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
