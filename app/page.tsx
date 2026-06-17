// Solvere V1 — single-scroll marketing page.
// Section order is locked to docs/BRIEF.md §5, with one addition:
// PayerMarquee inserted between The Number and The Gap. Team section
// removed pending real photos + credentials.

import { Nav } from "@/components/sections/Nav";
import { Hero } from "@/components/sections/Hero";
import { TheNumber } from "@/components/sections/TheNumber";
import { PayerMarquee } from "@/components/sections/PayerMarquee";
import { TheGap } from "@/components/sections/TheGap";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { RiskReversal } from "@/components/sections/RiskReversal";
import { WhySolvere } from "@/components/sections/WhySolvere";
import { FinalCta } from "@/components/sections/FinalCta";
import { Footer } from "@/components/sections/Footer";

export default function Home() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <TheNumber />
        <PayerMarquee />
        <TheGap />
        <HowItWorks />
        <RiskReversal />
        <WhySolvere />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
