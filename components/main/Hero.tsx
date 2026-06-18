// Hero — modern-sans headline (Inter 700, tight tracking) for the
// contemporary tech-product feel. Audit mockup stays in the right column.

import { BookACallButton } from "@/components/BookACallButton";
import { AuditMockup } from "@/components/AuditMockup";

const STAGGER = ["0ms", "80ms", "160ms", "240ms", "320ms"] as const;

export function Hero() {
  return (
    <section
      aria-label="Hero"
      className="bg-cream pt-[8vh] md:pt-[12vh] pb-7 md:pb-8"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <div className="md:grid md:grid-cols-12 md:gap-7 md:items-center">
          {/* Left — pitch */}
          <div className="md:col-span-7">
            <p
              className="solvere-fade-up font-sans uppercase text-caption-m md:text-caption-d text-teal"
              style={{ ["--solvere-delay" as string]: STAGGER[0] }}
            >
              ABU DHABI · UNITED ARAB EMIRATES
            </p>

            {/* LCP element — no opacity:0 entrance so Lighthouse measures from
                paint. Inter 700, tight tracking, large size for the modern
                tech-product gravitas the user asked for. */}
            <h1 className="mt-4 md:mt-5 font-sans font-bold text-ink text-[48px] md:text-[76px] leading-[1.04] tracking-[-0.025em]">
              A new standard for UAE claim recovery.
            </h1>

            <p
              className="solvere-fade-up mt-5 md:mt-6 max-w-[600px] font-sans text-muted text-body-lg-m md:text-body-lg-d"
              style={{ ["--solvere-delay" as string]: STAGGER[2] }}
            >
              Solvere uses AI agents and a DHA-licensed medical coder to
              recover the denied insurance claims your billers gave up on
              &mdash; end to end, every payer, pay only on recovery.
            </p>

            <div
              className="solvere-fade-up mt-7 md:mt-8 flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4"
              style={{ ["--solvere-delay" as string]: STAGGER[3] }}
            >
              <BookACallButton label="Book a 20-minute audit call" />
              <a
                href="#how-it-works"
                className="inline-flex items-center justify-center rounded-lg border border-ink/80 px-[28px] py-[14px] text-[17px] font-medium leading-none text-ink transition-colors duration-200 ease-out hover:bg-ink hover:text-cream"
              >
                See how it works
              </a>
            </div>

            <p
              className="solvere-fade-up mt-5 md:mt-6 font-sans uppercase text-caption-m md:text-caption-d text-muted"
              style={{ ["--solvere-delay" as string]: STAGGER[4] }}
            >
              No software · No integration · Pay only on recovery
            </p>
          </div>

          {/* Right — audit mockup */}
          <div
            className="solvere-fade-up md:col-span-5 mt-8 md:mt-0"
            style={{ ["--solvere-delay" as string]: STAGGER[1] }}
          >
            <div className="md:max-w-[420px] md:ml-auto">
              <AuditMockup />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
