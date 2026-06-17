// §7.2 — Hero. Cream bg. Asymmetric layout on desktop (text left · mockup right),
// stacked on mobile (text → mockup). CSS-only stagger on mount (§10).
//
// Two intentional deviations from the centered §7.2 spec, both inside DESIGN.md tokens:
//   • Container widens from max-w-hero (960px) to max-w-content (1140px) so the
//     mockup has room without compressing the headline column.
//   • Desktop headline scales from display-d (88px) to h1-d (56px). At 88px in a
//     ~620px column the headline wraps to 6 lines and reads as fragmented; H1 lets
//     it land in 2 lines and balances the mockup vertically. Mobile centred hero
//     keeps display-m (48px).

import { BookACallButton } from "@/components/BookACallButton";
import { AuditMockup } from "@/components/AuditMockup";

const STAGGER = ["0ms", "80ms", "160ms", "240ms", "320ms"] as const;

export function Hero() {
  return (
    <section
      aria-label="Hero"
      className="bg-cream pt-[6vh] md:pt-[8vh] pb-7 md:pb-9"
    >
      <div className="mx-auto max-w-content px-3 md:px-5">
        <div className="md:flex md:gap-5 md:items-center">
          {/* Left column — text */}
          <div className="md:flex-1 md:min-w-0 text-center md:text-left">
            <p
              className="solvere-fade-up font-sans uppercase text-caption-m md:text-caption-d text-teal"
              style={{ ["--solvere-delay" as string]: STAGGER[0] }}
            >
              ABU DHABI · UNITED ARAB EMIRATES
            </p>

            {/* H1 is the LCP element — must paint without an opacity:0 entrance
                or Lighthouse measures LCP from the animation end, not the paint. */}
            <h1 className="mt-3 font-display text-ink text-display-m md:text-h1-d md:leading-[1.05]">
              Recover the denied insurance claims your billers gave up on.
            </h1>

            <p
              className="solvere-fade-up mt-[20px] mx-auto md:mx-0 max-w-[580px] font-sans text-muted text-body-lg-m md:text-body-lg-d"
              style={{ ["--solvere-delay" as string]: STAGGER[2] }}
            >
              Solvere is the AI-native claim recovery service for UAE healthcare
              providers. We work your denied claims end-to-end and recover the
              money. You pay only when we win.
            </p>

            <div
              className="solvere-fade-up mt-[32px] flex justify-center md:justify-start"
              style={{ ["--solvere-delay" as string]: STAGGER[3] }}
            >
              <BookACallButton label="Book a 20-minute audit call" />
            </div>

            <p
              className="solvere-fade-up mt-2 font-sans uppercase text-caption-m md:text-caption-d text-muted"
              style={{ ["--solvere-delay" as string]: STAGGER[4] }}
            >
              No software · No integration · Pay only on recovery
            </p>
          </div>

          {/* Right column — audit mockup. Below trust line on mobile (mt-6),
              vertically centred alongside text on desktop. */}
          <div
            className="solvere-fade-up md:w-[400px] md:flex-shrink-0 mt-7 md:mt-0"
            style={{ ["--solvere-delay" as string]: STAGGER[1] }}
          >
            <AuditMockup />
          </div>
        </div>
      </div>
    </section>
  );
}
