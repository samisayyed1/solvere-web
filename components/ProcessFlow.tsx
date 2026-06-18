"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

const steps = [
  {
    no: "01",
    tag: "Export",
    title: "Send us 90 days of denied claims",
    body:
      "Your biller pulls the file from your billing system. One export, ten minutes of their time. We sign an NDA before the file moves.",
  },
  {
    no: "02",
    tag: "Audit",
    title: "We return a recoverability audit in five days",
    body:
      "Our AI agents classify every denial and score recoverability. A DHA-licensed coder verifies. You see the specific AED number we can recover from your data before you commit anything.",
  },
  {
    no: "03",
    tag: "Work",
    title: "We resubmit and appeal every workable claim",
    body:
      "End-to-end through eClaimLink and every UAE payer portal. Documentation, follow-up, escalation — all done by us. You get a monthly recovery report per payer.",
  },
  {
    no: "04",
    tag: "Paid",
    title: "You pay twenty percent of what lands",
    body:
      "And nothing else. No software fee, no setup fee, no retainer. If we recover zero, you owe zero. Cancel anytime, no termination fee.",
  },
];

export default function ProcessFlow() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 80%", "end 30%"],
  });
  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  return (
    <section id="how" className="relative bg-cream py-20 md:py-28">
      <div className="mx-auto max-w-container px-6 lg:px-10">
        <div className="max-w-[60ch] mb-14">
          <div className="eyebrow mb-5">How it works</div>
          <h2 className="h-serif text-[36px] sm:text-[46px] md:text-[58px] text-ink leading-[1.02]">
            Four steps. Five days to first audit.{" "}
            <span className="italic text-teal">Zero risk.</span>
          </h2>
        </div>

        {/* desktop timeline strip */}
        <div className="hidden md:flex items-center gap-4 mb-14">
          {steps.map((s, i) => (
            <div key={s.no} className="flex items-center flex-1">
              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-full border border-teal/40 grid place-items-center text-[11px] text-teal font-medium">
                  {s.no}
                </div>
                <span className="text-[11px] tracking-[0.22em] uppercase text-muted">
                  {s.tag}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div className="flex-1 mx-4 dot-line" />
              )}
            </div>
          ))}
        </div>

        <div ref={ref} className="relative grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-12">
          {/* vertical fill line (mobile + general accent on left) */}
          <div className="absolute left-[3px] top-2 bottom-2 w-px bg-rule md:hidden" />
          <motion.div
            style={{ height: lineHeight }}
            className="absolute left-[3px] top-2 w-px bg-teal md:hidden"
          />

          {steps.map((s, i) => (
            <motion.div
              key={s.no}
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.65, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
              className="pl-7 md:pl-0 relative"
            >
              <span className="md:hidden absolute left-0 top-2 w-1.5 h-1.5 rounded-full bg-teal" />
              <div className="hidden md:flex items-baseline gap-3 mb-5">
                <span className="h-display text-[12px] text-teal">{s.no}</span>
                <span className="text-[10px] tracking-[0.22em] uppercase text-muted">
                  {s.tag}
                </span>
              </div>
              <h3 className="h-serif text-[24px] md:text-[30px] text-ink leading-[1.15] mb-4">
                {s.title}
              </h3>
              <p className="text-[15px] md:text-[16px] leading-[1.6] text-muted max-w-[48ch]">
                {s.body}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
