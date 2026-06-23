"use client";

import { WhatsAppPillLight } from "./WhatsApp";

const cols = [
  {
    title: "Solvere",
    items: [
      { label: "How it works", href: "#dashboard" },
      { label: "What we do", href: "#capability" },
      { label: "Under the hood", href: "#deep-dive" },
      { label: "Founding cohort", href: "#founding" },
    ],
  },
  {
    title: "Contact",
    items: [
      { label: "hello@solvere.ai", href: "mailto:hello@solvere.ai" },
      { label: "Book an audit call", href: "#final-cta" },
      { label: "Apply to cohort", href: "#founding" },
    ],
  },
  {
    title: "Office",
    items: [
      { label: "Abu Dhabi, UAE", static: true },
      { label: "Sun–Thu · 09:00–18:00 GST", static: true },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="relative bg-cream-deep border-t border-rule">
      {/* TOP: brand + tagline + repeat CTA */}
      <div className="mx-auto max-w-container px-6 lg:px-10 pt-20 md:pt-24 pb-14 md:pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          <div className="lg:col-span-7">
            <div className="eyebrow mb-7">Get in touch</div>
            <div className="flex items-baseline gap-3 mb-7">
              <span className="h-serif text-[56px] md:text-[80px] lg:text-[100px] text-ink leading-none tracking-[-0.02em]">
                Solvere
              </span>
              <span className="w-2 h-2 rounded-full bg-teal mb-2" />
            </div>
            <p className="h-serif text-[22px] md:text-[26px] text-ink/85 italic max-w-[22ch] leading-[1.2]">
              What is owed is owed.
            </p>
            <p className="mt-4 text-[14px] text-muted leading-[1.6] max-w-[42ch]">
              The AI claim recovery service for UAE clinics. Built in Abu Dhabi,
              GCC-bound.
            </p>
          </div>

          <div className="lg:col-span-5 lg:justify-self-end w-full max-w-[440px]">
            <div className="rounded-2xl border border-rule bg-cream p-7 md:p-8">
              <div className="text-[10px] tracking-[0.22em] uppercase text-muted mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-teal" />
                Start the recovery
              </div>
              <p className="h-serif text-[22px] md:text-[26px] text-ink leading-[1.2] mb-6">
                Send us ninety days of denials. We return an audit in twenty-four hours.
              </p>
              <div className="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center">
                <a
                  href="#final-cta"
                  className="group inline-flex items-center justify-between gap-3 rounded-full bg-ink text-cream pl-5 pr-1.5 py-2 text-[14px] font-medium hover:bg-teal-deep transition-colors"
                >
                  Book a 20-minute audit call
                  <span className="grid place-items-center w-8 h-8 rounded-full bg-cream text-ink transition-transform group-hover:translate-x-0.5">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path
                        d="M1 6h10M6.5 1.5l4.5 4.5-4.5 4.5"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="square"
                      />
                    </svg>
                  </span>
                </a>
                <WhatsAppPillLight className="py-2 text-[14px]" />
              </div>
              <div className="mt-6 pt-5 border-t border-rule flex items-center justify-between text-[10px] tracking-[0.22em] uppercase text-muted">
                <span className="flex items-center gap-2">
                  <span className="w-1 h-1 rounded-full bg-teal" />
                  24-hour audit
                </span>
                <span>Pay only on recovery</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* MID: aligned columns */}
      <div className="border-t border-rule">
        <div className="mx-auto max-w-container px-6 lg:px-10 py-14 md:py-16">
          <div className="grid grid-cols-2 md:grid-cols-12 gap-10">
            {cols.map((c) => (
              <div key={c.title} className="md:col-span-3">
                <div className="text-[10px] tracking-[0.22em] uppercase text-muted mb-5">
                  {c.title}
                </div>
                <ul className="space-y-3">
                  {c.items.map((it) =>
                    "static" in it ? (
                      <li
                        key={it.label}
                        className="text-[14px] text-ink-soft leading-[1.5]"
                      >
                        {it.label}
                      </li>
                    ) : (
                      <li key={it.label}>
                        <a
                          href={it.href}
                          className="group inline-flex items-center gap-2 text-[14px] text-ink-soft hover:text-teal transition-colors"
                        >
                          <span>{it.label}</span>
                          <span className="opacity-0 group-hover:opacity-100 transition-opacity">
                            <svg
                              width="9"
                              height="9"
                              viewBox="0 0 9 9"
                              fill="none"
                            >
                              <path
                                d="M2 7l5-5M3 2h4v4"
                                stroke="currentColor"
                                strokeWidth="1.5"
                                strokeLinecap="square"
                              />
                            </svg>
                          </span>
                        </a>
                      </li>
                    )
                  )}
                </ul>
              </div>
            ))}

            <div className="col-span-2 md:col-span-3">
              <div className="text-[10px] tracking-[0.22em] uppercase text-muted mb-5">
                Compliance
              </div>
              <p className="text-[13px] text-muted leading-[1.65] max-w-[36ch]">
                DIFC Data Protection Law compliant. No protected health
                information is collected via this website. Sensitive data
                exchange occurs only after a signed NDA via secure encrypted
                channels.
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                <Chip>DIFC DP Law</Chip>
                <Chip>NDA-only</Chip>
                <Chip>DHA-licensed coding</Chip>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* BOTTOM bar */}
      <div className="border-t border-rule">
        <div className="mx-auto max-w-container px-6 lg:px-10 py-6 flex flex-col md:flex-row items-center justify-between gap-4 text-[11px] tracking-[0.18em] uppercase text-muted">
          <div className="flex items-center gap-5">
            <span>© 2026 Solvere</span>
            <Sep />
            <a href="#" className="hover:text-ink transition-colors">Privacy</a>
            <Sep />
            <a href="#" className="hover:text-ink transition-colors">Terms</a>
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-2">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full rounded-full bg-teal opacity-60 animate-ping" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal" />
              </span>
              Operating
            </span>
            <Sep />
            <span>v1.0 · 2026</span>
          </div>
        </div>
      </div>

      {/* Giant Solvere wordmark watermark */}
      <div
        aria-hidden
        className="overflow-hidden border-t border-rule"
      >
        <div className="mx-auto max-w-container px-6 lg:px-10 py-10 md:py-14 flex items-center justify-center">
          <div
            className="h-serif text-ink/[0.06] leading-none tracking-[-0.04em] select-none whitespace-nowrap"
            style={{ fontSize: "clamp(120px, 22vw, 320px)" }}
          >
            Solvere
          </div>
        </div>
      </div>
    </footer>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-rule bg-cream/60 px-2.5 py-1 text-[10px] tracking-[0.18em] uppercase text-muted">
      <span className="w-1 h-1 rounded-full bg-teal" />
      {children}
    </span>
  );
}

function Sep() {
  return <span aria-hidden className="w-1 h-1 rounded-full bg-rule" />;
}
