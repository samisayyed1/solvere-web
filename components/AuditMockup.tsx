// Static visual prop — renders like a real Recoverability Audit PDF a clinic
// would receive from Solvere. All figures are illustrative (marked SAMPLE).
// Sized for the hero right column. Pixel-sharp at any DPI; no <img>.

const ROWS = [
  { reason: "CPT-ICD mismatch", count: 312, value: "AED 612,400", conf: "High" },
  { reason: "Prior auth missing", count: 184, value: "AED 401,200", conf: "High" },
  { reason: "Eligibility lapse", count: 167, value: "AED 287,500", conf: "Medium" },
  { reason: "Bundling rule", count: 142, value: "AED 218,900", conf: "Medium" },
  { reason: "Documentation insufficient", count: 218, value: "AED 198,400", conf: "Medium" },
  { reason: "Code specificity", count: 124, value: "AED 142,300", conf: "Low" },
  { reason: "Filing deadline", count: 100, value: "AED 49,300", conf: "Low" },
] as const;

const CONF_TINT: Record<string, string> = {
  High: "bg-teal text-cream",
  Medium: "bg-teal/55 text-cream",
  Low: "bg-teal/25 text-ink-soft",
};

export function AuditMockup() {
  return (
    <div
      aria-hidden
      className="relative w-full mx-auto aspect-[5/7] rotate-[3deg] bg-cream border border-rule shadow-rule overflow-hidden flex flex-col"
    >
      {/* Header */}
      <div className="px-4 pt-4 pb-3 flex items-start justify-between gap-3 shrink-0">
        <p className="font-display font-medium text-[15px] leading-none text-ink">
          Solvere
        </p>
        <div className="text-right">
          <p className="font-sans text-[8px] uppercase tracking-[0.12em] text-muted">
            Recoverability Audit
          </p>
          <p className="mt-[3px] font-sans text-[9px] leading-tight text-ink-soft">
            Prepared for: Al Noor Polyclinic LLC
            <br />
            Karama, Dubai
          </p>
        </div>
      </div>
      <div className="border-t border-rule shrink-0" />

      {/* Period */}
      <div className="px-4 py-2.5 shrink-0">
        <p className="font-sans text-[8.5px] uppercase tracking-[0.12em] text-muted">
          Period
        </p>
        <p className="mt-1 font-sans text-[10px] text-ink-soft">
          Claims reviewed: 1,247 · 01 Aug — 31 Oct 2026
        </p>
      </div>

      {/* Headline stats */}
      <div className="px-4 py-2.5 grid grid-cols-3 gap-2 border-y border-rule shrink-0">
        {[
          { v: "AED 2.84M", l: "Reviewed" },
          { v: "AED 1.91M", l: "Recoverable" },
          { v: "67%", l: "Recovery rate" },
        ].map((s) => (
          <div key={s.l}>
            <p className="font-display text-teal text-[14px] leading-none">
              {s.v}
            </p>
            <p className="mt-1 font-sans text-[7.5px] uppercase tracking-[0.1em] text-muted">
              {s.l}
            </p>
          </div>
        ))}
      </div>

      {/* Denial table — flex-1 to absorb remaining space */}
      <div className="px-4 pt-2.5 flex-1 min-h-0 flex flex-col">
        <p className="font-sans text-[8px] uppercase tracking-[0.12em] text-muted shrink-0">
          Denial reasons
        </p>
        <div className="mt-1.5 flex-1 flex flex-col justify-around">
          {ROWS.map((r, i) => (
            <div
              key={r.reason}
              className={`flex items-center gap-2 py-[3px] ${
                i !== 0 ? "border-t border-rule/60" : ""
              }`}
            >
              <p className="flex-1 font-sans text-[9px] text-ink-soft truncate">
                {r.reason}
              </p>
              <p className="font-sans text-[8px] text-muted tabular-nums w-7 text-right">
                {r.count}
              </p>
              <p className="font-sans text-[8.5px] text-ink-soft tabular-nums w-[60px] text-right">
                {r.value}
              </p>
              <span
                className={`rounded-sm px-[5px] py-[1px] text-[7px] font-medium uppercase tracking-[0.08em] ${CONF_TINT[r.conf]}`}
              >
                {r.conf}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-rule shrink-0" />
      <div className="px-4 py-2 flex items-center justify-between shrink-0">
        <p className="font-sans text-[7.5px] uppercase tracking-[0.1em] text-muted">
          Solvere · 1WEB FZE · Abu Dhabi · DIFC-compliant
        </p>
        <p className="font-sans text-[7px] uppercase tracking-[0.14em] text-muted/70">
          Sample · Illustrative
        </p>
      </div>
    </div>
  );
}
