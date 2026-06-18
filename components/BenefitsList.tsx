"use client";

import { motion } from "framer-motion";

const items = [
  {
    no: "01",
    title: "Recover the cash your billers gave up on",
    body:
      "The 25–35% your team didn't have time to chase. Recovered into your account on Solvere's bandwidth, not yours.",
  },
  {
    no: "02",
    title: "Free your billing team for the work that's already clean",
    body:
      "Let your biller focus on submissions that go through first time. We handle the denials, the appeals, the payer escalation calls.",
  },
  {
    no: "03",
    title: "Trade write-offs for recovered revenue",
    body:
      "AED 800K to AED 1.4M per year, on average, for a clinic doing AED 20M revenue. Specific to your data after the 24-hour audit.",
  },
  {
    no: "04",
    title: "Maintain full visibility on every claim",
    body:
      "Claim-by-claim status, recovery rate, payer breakdown. Monthly recovery report delivered to the finance manager — no logins required.",
  },
  {
    no: "05",
    title: "Keep the workflow you already have",
    body:
      "No PMS integration. No software to install. No new tab for your team to learn. Your biller exports a file. That's the entire ask.",
  },
];

export default function BenefitsList() {
  return (
    <section className="bg-cream-deep border-y border-rule py-20 md:py-28">
      <div className="mx-auto max-w-container px-6 lg:px-10">
        <div className="max-w-[60ch] mb-14">
          <div className="eyebrow mb-5">What changes</div>
          <h2 className="h-serif text-[36px] sm:text-[46px] md:text-[58px] text-ink leading-[1.02]">
            What you get back when Solvere{" "}
            <span className="italic text-teal">takes the denials.</span>
          </h2>
        </div>

        <div className="divide-y divide-rule border-y border-rule">
          {items.map((it, i) => (
            <motion.div
              key={it.no}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.55, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }}
              className="grid grid-cols-[auto_1fr] md:grid-cols-[80px_1fr_1.4fr] gap-6 md:gap-12 items-start py-8 md:py-10 group"
            >
              <div className="h-display text-[18px] text-teal pt-1">{it.no}</div>
              <h3 className="h-serif text-[22px] md:text-[26px] text-ink leading-[1.2] col-start-2">
                {it.title}
              </h3>
              <p className="text-[15px] md:text-[16px] text-muted leading-[1.6] col-start-2 md:col-start-3 md:col-end-4 md:row-start-1">
                {it.body}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
