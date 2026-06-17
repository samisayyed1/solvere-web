// Static visual prop — renders like a real Recoverability Audit PDF a clinic
// would receive from Solvere. All figures are illustrative (marked SAMPLE).
// Sized for the hero right column. Pixel-sharp at any DPI; no <img>.
//
// All internal paddings use explicit [Npx] arbitrary values because the
// Tailwind spacing scale here is keyed to the page-level 8pt grid (5 = 48px),
// which is too coarse for an internal document layout.

const ROWS = [
  { reason: "CPT–ICD mismatch", value: "AED 612,400", conf: "High" },
  { reason: "Prior auth missing", value: "AED 401,200", conf: "High" },
  { reason: "Eligibility lapse", value: "AED 287,500", conf: "Medium" },
  { reason: "Bundling rule", value: "AED 218,900", conf: "Medium" },
  { reason: "Documentation", value: "AED 198,400", conf: "Medium" },
  { reason: "Code specificity", value: "AED 142,300", conf: "Low" },
  { reason: "Filing deadline", value: "AED 49,300", conf: "Low" },
] as const;

const CONF_TINT: Record<string, string> = {
  High: "bg-teal text-cream",
  Medium: "bg-teal/55 text-cream",
  Low: "bg-teal/20 text-ink-soft",
};

export function AuditMockup() {
  return (
    <div
      aria-hidden
      className="relative w-full mx-auto aspect-[5/7] rotate-[3deg] bg-cream border border-rule shadow-rule overflow-hidden flex flex-col"
    >
      {/* Header — wordmark + audit metadata */}
      <div className="px-5 pt-[18px] pb-[14px] flex items-start justify-between gap-3 shrink-0">
        <p className="font-display font-medium text-[18px] leading-none text-ink">
          Solvere
        </p>
        <div className="text-right">
          <p className="font-sans text-[8.5px] uppercase tracking-[0.18em] text-muted">
            Recoverability Audit
          </p>
          <p className="mt-[6px] font-sans text-[9.5px] leading-[1.5] text-ink-soft">
            Al Noor Polyclinic LLC
            <br />
            Karama, Dubai
          </p>
        </div>
      </div>
      <div className="border-t border-rule shrink-0" />

      {/* Period block */}
      <div className="px-5 py-[12px] shrink-0">
        <p className="font-sans text-[8.5px] uppercase tracking-[0.18em] text-muted">
          Period
        </p>
        <p className="mt-[6px] font-sans text-[10.5px] text-ink-soft tabular-nums">
          1,247 claims · 01 Aug — 31 Oct 2026
        </p>
      </div>
      <div className="border-t border-rule shrink-0" />

      {/* Headline stats — three columns, vertical hairlines between */}
      <div className="grid grid-cols-3 shrink-0 divide-x divide-rule/80">
        {[
          { v: "AED 2.84M", l: "Reviewed" },
          { v: "AED 1.91M", l: "Recoverable" },
          { v: "67%", l: "Recovery" },
        ].map((s) => (
          <div key={s.l} className="px-2 py-[16px] text-center">
            <p className="font-display text-teal text-[16px] leading-none tabular-nums">
              {s.v}
            </p>
            <p className="mt-[10px] font-sans text-[7.5px] uppercase tracking-[0.16em] text-muted">
              {s.l}
            </p>
          </div>
        ))}
      </div>
      <div className="border-t border-rule shrink-0" />

      {/* Denial reasons table — flex-1 absorbs remaining space.
          Each row uses tight px padding so 7 rows fit comfortably with
          generous outer breathing room above + below. */}
      <div className="px-5 pt-[14px] pb-[10px] flex-1 min-h-0 flex flex-col">
        <p className="font-sans text-[8.5px] uppercase tracking-[0.18em] text-muted shrink-0">
          Top denial reasons
        </p>
        <div className="mt-[10px] flex-1 flex flex-col">
          {ROWS.map((r, i) => (
            <div
              key={r.reason}
              className={`flex items-center gap-3 py-[7px] ${
                i !== 0 ? "border-t border-rule/60" : ""
              }`}
            >
              <p className="flex-1 font-sans text-[10px] text-ink-soft whitespace-nowrap">
                {r.reason}
              </p>
              <p className="font-sans text-[9.5px] text-ink-soft tabular-nums w-[72px] text-right">
                {r.value}
              </p>
              <span
                className={`rounded-sm px-[6px] py-[2px] text-[7px] font-medium uppercase tracking-[0.12em] w-[44px] text-center ${CONF_TINT[r.conf]}`}
              >
                {r.conf}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-rule shrink-0" />
      <div className="px-5 py-[10px] flex items-center justify-between shrink-0">
        <p className="font-sans text-[7.5px] uppercase tracking-[0.18em] text-muted">
          Solvere · 1WEB FZE · Abu Dhabi
        </p>
        <p className="font-sans text-[7.5px] uppercase tracking-[0.2em] text-muted/60">
          Sample
        </p>
      </div>
    </div>
  );
}
