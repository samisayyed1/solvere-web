"use client";

import { motion } from "framer-motion";

const pillars = [
  {
    no: "01",
    tag: "End-to-end recovery",
    title: "We work your denied claims from export to recovered payment.",
    body:
      "Classification, documentation, resubmission, appeals, payer follow-up — handled. You hand us 90 days of denials and step away until cash lands in the clinic's account.",
  },
  {
    no: "02",
    tag: "AI plus licensed coding",
    title: "AI scores recoverability across hundreds of claims in minutes.",
    body:
      "A DHA-licensed medical coder verifies every high-value or complex submission before it goes back to the payer. AI does the volume. A human does the judgement.",
  },
  {
    no: "03",
    tag: "Every UAE payer portal",
    title: "Daman, Thiqa, NEXtCARE, NAS, MedNet — and the rest of them.",
    body:
      "We file resubmissions and appeals through eClaimLink and every major UAE payer portal. We learn each payer's denial patterns claim by claim, so the next recovery is faster than the last.",
  },
  {
    no: "04",
    tag: "Pay only on recovery",
    title: "Twenty percent of recovered cash. Nothing else.",
    body:
      "No setup fee. No software fee. No retainer. If Solvere recovers nothing, you pay nothing. The only thing you risk is the ten minutes it takes your biller to export the file.",
  },
];

export default function CapabilityStack() {
  return (
    <section
      id="capability"
      className="bg-cream-deep border-y border-rule py-20 md:py-28"
    >
      <div className="mx-auto max-w-container px-6 lg:px-10">
        <div className="max-w-[60ch] mb-14">
          <div className="eyebrow mb-5">What Solvere does</div>
          <h2 className="h-serif text-[36px] sm:text-[46px] md:text-[58px] text-ink">
            Four pillars.
            <br />
            One outcome:{" "}
            <span className="text-teal italic">cash in your account.</span>
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-rule rounded-2xl overflow-hidden border border-rule">
          {pillars.map((p, i) => (
            <motion.div
              key={p.no}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
              className="bg-cream-deep p-8 md:p-10 group hover:bg-cream transition-colors"
            >
              <div className="flex items-center gap-3 mb-6">
                <span className="h-display text-[14px] text-teal">{p.no}</span>
                <span className="flex-1 h-px bg-rule" />
                <span className="text-[10px] tracking-[0.22em] uppercase text-muted">
                  {p.tag}
                </span>
              </div>
              <h3 className="h-serif text-[22px] md:text-[26px] text-ink leading-[1.15] mb-4">
                {p.title}
              </h3>
              <p className="text-[15px] md:text-[16px] leading-[1.6] text-muted">
                {p.body}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
