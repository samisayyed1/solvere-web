// Comparison table — "Solvere vs. doing it yourself."
// Real <table> for accessibility (proper thead/th/scope). Crisp tick marks
// vs em-dashes. No vague "Better than competitors" claims — every row is
// a specific capability the buyer is making a decision on.

import { FadeIn } from "@/components/FadeIn";

type Cell = { kind: "yes"; label?: string } | { kind: "no" } | { kind: "partial"; label: string };

const ROWS: Array<{ capability: string; diy: Cell; solvere: Cell }> = [
  {
    capability: "End-to-end claim recovery (resubmission + appeal + follow-up)",
    diy: { kind: "partial", label: "Partial" },
    solvere: { kind: "yes" },
  },
  {
    capability: "AI triage of denied claims by reason and recoverability",
    diy: { kind: "no" },
    solvere: { kind: "yes" },
  },
  {
    capability: "DHA-licensed medical coder verification on every claim",
    diy: { kind: "partial", label: "Depends" },
    solvere: { kind: "yes" },
  },
  {
    capability: "Coverage across every major UAE payer portal",
    diy: { kind: "partial", label: "Manual" },
    solvere: { kind: "yes" },
  },
  {
    capability: "Pay only on recovery (no upfront fee, no software cost)",
    diy: { kind: "no" },
    solvere: { kind: "yes" },
  },
  {
    capability: "Software install or PMS integration required",
    diy: { kind: "partial", label: "Often" },
    solvere: { kind: "no" },
  },
  {
    capability: "Free recoverability audit before any commitment",
    diy: { kind: "no" },
    solvere: { kind: "yes", label: "5-day" },
  },
  {
    capability: "Direct founder access for issues and escalation",
    diy: { kind: "no" },
    solvere: { kind: "yes", label: "Founding cohort" },
  },
];

function YesMark({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 justify-center md:justify-start">
      <span
        aria-hidden
        className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-teal text-cream"
      >
        <svg viewBox="0 0 12 12" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2.5 6.5l2.5 2.5 4.5-5" />
        </svg>
      </span>
      {label ? (
        <span className="font-sans text-ink text-body-m md:text-body-d">
          {label}
        </span>
      ) : (
        <span className="sr-only">Yes</span>
      )}
    </div>
  );
}

function NoMark() {
  return (
    <div className="flex items-center gap-2 justify-center md:justify-start">
      <span
        aria-hidden
        className="inline-flex items-center justify-center h-5 w-5 rounded-full border border-rule"
      >
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5 text-muted" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M3 6h6" />
        </svg>
      </span>
      <span className="sr-only">No</span>
    </div>
  );
}

function PartialMark({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 justify-center md:justify-start">
      <span
        aria-hidden
        className="inline-flex items-center justify-center h-5 w-5 rounded-full border border-amber/50 bg-amber/10"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-amber" />
      </span>
      <span className="font-sans italic text-muted text-body-m md:text-body-d">
        {label}
      </span>
    </div>
  );
}

function renderCell(c: Cell) {
  if (c.kind === "yes") return <YesMark label={c.label} />;
  if (c.kind === "no") return <NoMark />;
  return <PartialMark label={c.label} />;
}

export function Comparison() {
  return (
    <section
      aria-label="Solvere versus doing it yourself"
      className="bg-cream py-7 md:py-8 border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            HOW IT COMPARES
          </p>
          <h2 className="mt-3 md:mt-4 font-sans font-bold text-ink text-[36px] md:text-[56px] leading-[1.05] tracking-[-0.02em]">
            Solvere vs. doing it yourself.
          </h2>
          <p className="mt-4 md:mt-5 font-sans text-muted text-body-m md:text-body-lg-d max-w-prose">
            The decision isn&apos;t whether to recover denied claims &mdash;
            you&apos;ve already paid your biller to try. The decision is
            whether to chase the rest at marginal cost or write them off.
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-7 md:mt-8">
          <div className="overflow-x-auto -mx-3 md:mx-0 px-3 md:px-0">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-y border-rule">
                  <th
                    scope="col"
                    className="text-left py-3 md:py-4 pr-3 md:pr-5 font-sans uppercase tracking-[0.14em] text-caption-m md:text-caption-d text-muted"
                  >
                    Capability
                  </th>
                  <th
                    scope="col"
                    className="text-left py-3 md:py-4 px-3 md:px-5 font-sans uppercase tracking-[0.14em] text-caption-m md:text-caption-d text-muted"
                  >
                    Doing it yourself
                  </th>
                  <th
                    scope="col"
                    className="text-left py-3 md:py-4 px-3 md:px-5 font-sans uppercase tracking-[0.14em] text-caption-m md:text-caption-d text-teal"
                  >
                    Solvere
                  </th>
                </tr>
              </thead>
              <tbody>
                {ROWS.map((r) => (
                  <tr key={r.capability} className="border-b border-rule">
                    <th
                      scope="row"
                      className="text-left align-top py-4 md:py-5 pr-3 md:pr-5 font-sans font-medium text-ink text-body-m md:text-body-d max-w-prose"
                    >
                      {r.capability}
                    </th>
                    <td className="align-top py-4 md:py-5 px-3 md:px-5">
                      {renderCell(r.diy)}
                    </td>
                    <td className="align-top py-4 md:py-5 px-3 md:px-5">
                      {renderCell(r.solvere)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}
