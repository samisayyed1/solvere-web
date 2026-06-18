// V1 — Original Solvere site, preserved end-to-end.
// Accessible at /v1. Main route at / is the new Amperos-modeled build.

import { Nav } from "@/components/sections/Nav";
import { Hero } from "@/components/sections/Hero";
import { CapabilityGrid } from "@/components/sections/CapabilityGrid";
import { TheNumber } from "@/components/sections/TheNumber";
import { PayerMarquee } from "@/components/sections/PayerMarquee";
import { TheGap } from "@/components/sections/TheGap";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { OutcomesGrid } from "@/components/sections/OutcomesGrid";
import { RiskReversal } from "@/components/sections/RiskReversal";
import { AIPlusHuman } from "@/components/sections/AIPlusHuman";
import { WhySolvere } from "@/components/sections/WhySolvere";
import { FinalCta } from "@/components/sections/FinalCta";
import { Footer } from "@/components/sections/Footer";

export default function V1Page() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <CapabilityGrid />
        <TheNumber />
        <PayerMarquee />
        <TheGap />
        <HowItWorks />
        <OutcomesGrid />
        <RiskReversal />
        <AIPlusHuman />
        <WhySolvere />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
