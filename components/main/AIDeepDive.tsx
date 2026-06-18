"use client";

// Interactive tab pane — 4 dimensions of how Solvere works under the hood.
// Click or use ArrowUp/ArrowDown to switch tabs. Each tab opens a large
// content pane with title, body and a small geometric illustration.
//
// All shapes are abstract / geometric — no medical iconography per
// FORBIDDEN.md. Each shape is a metaphor for the dimension it sits beside:
// triage = funnel of dots, verification = checkmark on rect, execution =
// three connected nodes, learning = ascending bars.

import { useEffect, useRef, useState } from "react";
import { FadeIn } from "@/components/FadeIn";

type TabId = "triage" | "verify" | "execute" | "learn";

const TABS: Array<{
  id: TabId;
  eyebrow: string;
  label: string;
  title: string;
  body: string;
}> = [
  {
    id: "triage",
    eyebrow: "TRIAGE",
    label: "AI reads every denial",
    title: "AI reads every denied claim.",
    body:
      "Classification, reason coding, recoverability scoring across hundreds of claims at once. The work that used to take a biller a week happens in minutes — without missing anything that pays.",
  },
  {
    id: "verify",
    eyebrow: "VERIFICATION",
    label: "A licensed coder approves",
    title: "A DHA-licensed coder verifies before submission.",
    body:
      "Every high-value or complex claim is reviewed by a UAE-licensed medical coder before it goes back to the payer. The human gate before the payer gateway. Nothing leaves the building unchecked.",
  },
  {
    id: "execute",
    eyebrow: "EXECUTION",
    label: "Every payer's portal",
    title: "End-to-end through every payer portal.",
    body:
      "Resubmission and appeal through eClaimLink, Daman, Thiqa, NEXtCARE, NAS, MedNet, ADNIC, Sukoon and the rest. Documentation, follow-up, escalation — handled to outcome, not just to send.",
  },
  {
    id: "learn",
    eyebrow: "LEARNING",
    label: "Every recovery trains the next",
    title: "The system gets sharper every cycle.",
    body:
      "Each payer response updates the rule library. After ten thousand claims, our denial-reason knowledge becomes the moat: nobody else in the GCC can rebuild it quickly.",
  },
];

function TabIllustration({ id }: { id: TabId }) {
  // Abstract geometric SVGs — one per tab. Cream stroke on ink panel.
  const common = "w-full h-full text-teal";
  switch (id) {
    case "triage":
      // Funnel of dots — many in, sorted out
      return (
        <svg viewBox="0 0 200 160" className={common} fill="none" stroke="currentColor" aria-hidden>
          {/* Funnel outline */}
          <path d="M20 30 L180 30 L120 100 L120 140 L80 140 L80 100 Z" strokeWidth="1.5" opacity="0.4" />
          {/* Top input dots */}
          {[40, 60, 80, 100, 120, 140, 160].map((x) => (
            <circle key={x} cx={x} cy="20" r="3" fill="currentColor" opacity="0.6" />
          ))}
          {/* Mid-funnel dots */}
          {[70, 90, 110, 130].map((x) => (
            <circle key={x} cx={x} cy="65" r="2.5" fill="currentColor" />
          ))}
          {/* Output dots */}
          <circle cx="100" cy="120" r="3" fill="currentColor" />
          <circle cx="100" cy="135" r="3" fill="currentColor" />
        </svg>
      );
    case "verify":
      // Document with checkmark
      return (
        <svg viewBox="0 0 200 160" className={common} fill="none" stroke="currentColor" aria-hidden>
          <rect x="50" y="20" width="100" height="120" strokeWidth="1.5" opacity="0.4" rx="4" />
          {[40, 55, 70, 90].map((y) => (
            <line key={y} x1="62" y1={y} x2="138" y2={y} strokeWidth="1.2" opacity="0.5" />
          ))}
          {/* Big check */}
          <circle cx="100" cy="115" r="18" fill="currentColor" />
          <path d="M88 115 L96 122 L112 108" stroke="#F8F6F1" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "execute":
      // Three connected nodes
      return (
        <svg viewBox="0 0 200 160" className={common} fill="none" stroke="currentColor" aria-hidden>
          <line x1="30" y1="80" x2="100" y2="80" strokeWidth="1.5" opacity="0.5" />
          <line x1="100" y1="80" x2="170" y2="80" strokeWidth="1.5" opacity="0.5" />
          <line x1="100" y1="80" x2="100" y2="130" strokeWidth="1.5" opacity="0.5" />
          <circle cx="30" cy="80" r="9" fill="currentColor" />
          <circle cx="100" cy="80" r="11" fill="currentColor" />
          <circle cx="170" cy="80" r="9" fill="currentColor" />
          <circle cx="100" cy="130" r="9" fill="currentColor" />
          {/* Outer ring */}
          <circle cx="30" cy="80" r="16" strokeWidth="1.2" opacity="0.4" />
          <circle cx="100" cy="80" r="20" strokeWidth="1.2" opacity="0.4" />
          <circle cx="170" cy="80" r="16" strokeWidth="1.2" opacity="0.4" />
          <circle cx="100" cy="130" r="16" strokeWidth="1.2" opacity="0.4" />
        </svg>
      );
    case "learn":
      // Ascending bars
      return (
        <svg viewBox="0 0 200 160" className={common} fill="none" stroke="currentColor" aria-hidden>
          <line x1="20" y1="140" x2="180" y2="140" strokeWidth="1.2" opacity="0.5" />
          {[
            { x: 40, h: 30 },
            { x: 70, h: 55 },
            { x: 100, h: 75 },
            { x: 130, h: 95 },
            { x: 160, h: 110 },
          ].map((b) => (
            <rect
              key={b.x}
              x={b.x - 10}
              y={140 - b.h}
              width="20"
              height={b.h}
              fill="currentColor"
              opacity={0.4 + (b.h / 110) * 0.6}
            />
          ))}
        </svg>
      );
  }
}

export function AIDeepDive() {
  const [active, setActive] = useState<number>(0);
  const tablistRef = useRef<HTMLDivElement | null>(null);

  // Keyboard navigation per WAI-ARIA tabs pattern
  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown" || e.key === "ArrowRight") {
      e.preventDefault();
      setActive((i) => (i + 1) % TABS.length);
    } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
      e.preventDefault();
      setActive((i) => (i - 1 + TABS.length) % TABS.length);
    } else if (e.key === "Home") {
      e.preventDefault();
      setActive(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setActive(TABS.length - 1);
    }
  }

  // Focus the new tab button when active changes via keyboard
  useEffect(() => {
    const tabs = tablistRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
    tabs?.[active]?.focus({ preventScroll: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  const current = TABS[active];

  return (
    <section
      aria-label="How recovery works under the hood"
      className="bg-ink py-7 md:py-8 border-t border-cream/10"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            UNDER THE HOOD
          </p>
          <h2 className="mt-3 md:mt-4 font-sans font-bold text-cream text-[36px] md:text-[56px] leading-[1.05] tracking-[-0.02em]">
            AI-native recovery, human-verified.
          </h2>
          <p className="mt-4 md:mt-5 font-sans text-cream/70 text-body-m md:text-body-lg-d max-w-prose">
            Pure-AI vendors miss what the rules don&apos;t cover. Pure-human
            shops can&apos;t scale. Solvere ships both, in the same loop.
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-7 md:mt-8">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 md:gap-7 border-t border-cream/10 pt-6 md:pt-7">
            {/* Tablist */}
            <div
              role="tablist"
              aria-label="Solvere capability dimensions"
              ref={tablistRef}
              onKeyDown={onKeyDown}
              className="md:col-span-4 flex md:flex-col gap-2 overflow-x-auto md:overflow-visible -mx-3 px-3 md:mx-0 md:px-0 pb-2 md:pb-0"
            >
              {TABS.map((t, i) => {
                const selected = i === active;
                return (
                  <button
                    key={t.id}
                    role="tab"
                    aria-selected={selected}
                    aria-controls={`tabpanel-${t.id}`}
                    id={`tab-${t.id}`}
                    tabIndex={selected ? 0 : -1}
                    onClick={() => setActive(i)}
                    className={[
                      "shrink-0 md:shrink text-left rounded-lg px-4 py-3 md:px-5 md:py-4 transition-colors duration-200 ease-out border",
                      selected
                        ? "bg-ink-soft border-teal/60 text-cream"
                        : "bg-transparent border-cream/10 text-cream/65 hover:text-cream hover:border-cream/25",
                    ].join(" ")}
                  >
                    <p
                      className={[
                        "font-sans uppercase tracking-[0.14em] text-[10px] md:text-[11px]",
                        selected ? "text-teal" : "text-cream/45",
                      ].join(" ")}
                    >
                      {t.eyebrow}
                    </p>
                    <p className="mt-1.5 font-sans font-medium text-[14px] md:text-[15px]">
                      {t.label}
                    </p>
                  </button>
                );
              })}
            </div>

            {/* Active pane */}
            <div
              role="tabpanel"
              id={`tabpanel-${current.id}`}
              aria-labelledby={`tab-${current.id}`}
              className="md:col-span-8 rounded-xl border border-cream/10 bg-ink-soft/60 p-5 md:p-7 min-h-[320px] md:min-h-[400px]"
            >
              <div className="grid grid-cols-1 md:grid-cols-5 gap-5 md:gap-6 h-full">
                <div className="md:col-span-3 flex flex-col">
                  <p className="font-sans uppercase tracking-[0.16em] text-teal text-caption-m md:text-caption-d">
                    {current.eyebrow}
                  </p>
                  <h3 className="mt-3 font-sans font-bold text-cream text-h3-m md:text-h2-d tracking-[-0.015em] leading-[1.1]">
                    {current.title}
                  </h3>
                  <p className="mt-4 font-sans text-cream/75 text-body-m md:text-body-lg-d max-w-prose">
                    {current.body}
                  </p>
                </div>
                <div className="md:col-span-2 flex items-center justify-center min-h-[160px]">
                  <div className="w-full max-w-[240px] aspect-[4/3]">
                    <TabIllustration id={current.id} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}
