// Solvere Dashboard mockup — kanban-style view of fake claims moving
// through the recovery pipeline. Premium product moment even pre-launch.
//
// All data illustrative — see "SAMPLE · ILLUSTRATIVE" badge.
// Static (no JS), uses brand tokens only. Generates its own visual
// gravity by sheer density of legitimate-looking detail.

import { FadeIn } from "@/components/FadeIn";

type Stage = "received" | "review" | "resubmitted" | "recovered";

const COLUMNS: Array<{ id: Stage; title: string; tint: string }> = [
  { id: "received", title: "Received", tint: "text-muted" },
  { id: "review", title: "In review", tint: "text-amber" },
  { id: "resubmitted", title: "Resubmitted", tint: "text-teal" },
  { id: "recovered", title: "Recovered", tint: "text-teal" },
];

type Claim = {
  ref: string;
  payer: string;
  amount: string;
  reason: string;
  stage: Stage;
  done?: boolean;
};

const CLAIMS: Claim[] = [
  { ref: "DM-24891", payer: "NAS",      amount: "AED 4,200",  reason: "Eligibility lapse",         stage: "received" },
  { ref: "DM-24827", payer: "MedNet",   amount: "AED 3,100",  reason: "Code specificity",          stage: "received" },
  { ref: "DM-24814", payer: "Daman",    amount: "AED 18,400", reason: "Bundling rule",             stage: "received" },
  { ref: "DM-24802", payer: "NEXtCARE", amount: "AED 6,800",  reason: "Prior auth missing",        stage: "received" },

  { ref: "DM-24773", payer: "Daman",    amount: "AED 12,800", reason: "Documentation insufficient", stage: "review" },
  { ref: "DM-24759", payer: "ADNIC",    amount: "AED 7,200",  reason: "CPT–ICD mismatch",          stage: "review" },
  { ref: "DM-24744", payer: "Thiqa",    amount: "AED 5,800",  reason: "Filing deadline",           stage: "review" },

  { ref: "DM-24712", payer: "Thiqa",    amount: "AED 8,400",  reason: "Resubmitted with fix",      stage: "resubmitted" },
  { ref: "DM-24698", payer: "Daman",    amount: "AED 22,500", reason: "Appeal filed",              stage: "resubmitted" },
  { ref: "DM-24681", payer: "NAS",      amount: "AED 4,900",  reason: "Awaiting payer response",   stage: "resubmitted" },

  { ref: "DM-24612", payer: "NEXtCARE", amount: "AED 6,100",  reason: "Paid in full",              stage: "recovered", done: true },
  { ref: "DM-24587", payer: "Daman",    amount: "AED 18,900", reason: "Paid in full",              stage: "recovered", done: true },
  { ref: "DM-24574", payer: "MedNet",   amount: "AED 9,300",  reason: "Paid (partial appeal)",     stage: "recovered", done: true },
  { ref: "DM-24561", payer: "Thiqa",    amount: "AED 11,200", reason: "Paid in full",              stage: "recovered", done: true },
];

function CountForStage(stage: Stage) {
  return CLAIMS.filter((c) => c.stage === stage).length;
}

function ClaimsForStage(stage: Stage) {
  return CLAIMS.filter((c) => c.stage === stage);
}

function CheckIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 12 12"
      className="h-3 w-3 shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2.5 6.5l2.5 2.5 4.5-5" />
    </svg>
  );
}

export function SolvereDashboard() {
  return (
    <section
      aria-label="Solvere claim pipeline"
      className="relative bg-ink py-7 md:py-8 border-t border-cream/10"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <FadeIn className="max-w-narrow">
          <p className="font-sans uppercase text-caption-m md:text-caption-d text-teal">
            INSIDE SOLVERE
          </p>
          <h2 className="mt-3 md:mt-4 font-sans font-bold text-cream text-[36px] md:text-[56px] leading-[1.05] tracking-[-0.02em]">
            See claims move through Solvere.
          </h2>
          <p className="mt-4 md:mt-5 font-sans text-cream/70 text-body-m md:text-body-lg-d max-w-prose">
            Every denied claim moves through four stages. AI agents triage,
            a DHA-licensed coder verifies, payer portals receive the
            resubmission, the wire lands. You see all of it.
          </p>
        </FadeIn>

        <FadeIn delay={0.08} className="mt-7 md:mt-8">
          <div className="relative rounded-xl border border-cream/10 bg-ink-soft/60 backdrop-blur-sm overflow-hidden">
            {/* Sample badge — top right */}
            <div className="absolute top-3 right-3 md:top-4 md:right-4 z-10">
              <span className="inline-flex items-center gap-1.5 rounded-md border border-amber/40 bg-ink/80 px-2 py-[3px] font-sans text-[9px] uppercase tracking-[0.18em] text-amber">
                <span aria-hidden className="h-1 w-1 rounded-full bg-amber" />
                Sample · Illustrative
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4">
              {COLUMNS.map((col) => {
                const claims = ClaimsForStage(col.id);
                return (
                  <div
                    key={col.id}
                    className="border-t md:border-t-0 md:border-l border-cream/10 first:border-t-0 first:md:border-l-0"
                  >
                    {/* Column header */}
                    <div className="px-4 md:px-5 py-3 md:py-4 border-b border-cream/10 flex items-center justify-between">
                      <p className={`font-sans uppercase tracking-[0.14em] text-[11px] md:text-[12px] font-medium ${col.tint}`}>
                        {col.title}
                      </p>
                      <p className="font-sans text-cream/45 text-[11px] tabular-nums">
                        {CountForStage(col.id)}
                      </p>
                    </div>

                    {/* Column cards */}
                    <div className="p-3 md:p-4 space-y-2.5 md:space-y-3">
                      {claims.map((c) => (
                        <article
                          key={c.ref}
                          className="rounded-md border border-cream/10 bg-ink p-3 hover:border-teal/40 transition-colors duration-150"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <p className="font-sans font-medium text-cream text-[12px]">
                              {c.payer}
                            </p>
                            <p className="font-sans text-cream/40 text-[10px] tabular-nums">
                              {c.ref}
                            </p>
                          </div>
                          <p className="mt-1.5 font-sans text-cream font-medium text-[14px] tabular-nums">
                            {c.amount}
                          </p>
                          <div className="mt-1.5 flex items-center gap-1.5">
                            {c.done ? (
                              <span className="text-teal">
                                <CheckIcon />
                              </span>
                            ) : (
                              <span
                                aria-hidden
                                className="h-1 w-1 rounded-full bg-cream/30 shrink-0"
                              />
                            )}
                            <p className="font-sans text-cream/55 text-[10.5px] truncate">
                              {c.reason}
                            </p>
                          </div>
                        </article>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </FadeIn>

        {/* Caption row beneath the dashboard */}
        <FadeIn delay={0.16} className="mt-5 md:mt-6">
          <p className="font-sans text-cream/55 text-caption-m md:text-caption-d uppercase tracking-[0.14em] text-center">
            Real claims move in real time once Solvere is running. This is the view you receive monthly.
          </p>
        </FadeIn>
      </div>
    </section>
  );
}
