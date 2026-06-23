"use client";

const items = [
  "Abu Dhabi · UAE",
  "DHA-licensed coding",
  "DIFC Data Protection compliant",
  "eClaimLink + payer portals",
];

export default function TrustBand() {
  return (
    <section className="bg-cream-deep border-y border-rule">
      <div className="mx-auto max-w-container px-6 lg:px-10 py-5 md:py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-3 gap-x-6">
          {items.map((label) => (
            <div
              key={label}
              className="flex items-center gap-2 text-[11px] tracking-[0.22em] uppercase text-muted"
            >
              <svg
                width="10"
                height="10"
                viewBox="0 0 10 10"
                className="text-teal flex-none"
                fill="none"
              >
                <path
                  d="M1.5 5.5l2.5 2.5L8.5 2.5"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="square"
                />
              </svg>
              {label}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
