"use client";

const payers = [
  "Daman", "Thiqa", "NEXtCARE", "NAS", "MedNet", "ADNIC", "Sukoon",
  "Orient", "Oman Insurance", "Bupa Arabia", "MetLife", "AXA", "Cigna",
  "Now Health", "Mednet Global", "AAFAQ", "Saico", "National General",
];

export default function PayerMarquee() {
  const seq = [...payers, ...payers];
  return (
    <section className="bg-cream py-16 md:py-20 overflow-hidden">
      <div className="mx-auto max-w-container px-6 lg:px-10 mb-8">
        <div className="eyebrow">Payers we work</div>
      </div>
      <div className="relative">
        <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-20 z-10 bg-gradient-to-r from-cream to-transparent" />
        <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-20 z-10 bg-gradient-to-l from-cream to-transparent" />
        <div className="flex marquee-track gap-12 whitespace-nowrap">
          {seq.map((p, i) => (
            <div key={i} className="flex items-center gap-12">
              <span className="h-serif text-[30px] md:text-[38px] text-muted/85 hover:text-ink transition-colors">
                {p}
              </span>
              <span className="text-teal/50">·</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
