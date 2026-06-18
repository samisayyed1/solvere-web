// Solvere main marketing site. Modern B2B SaaS layout patterns adapted
// to the Solvere brand tokens and the playbook copy.
//
// Old V1 (the long single-scroll version with audit mockup in hero column)
// is preserved at /v1.

import { Nav } from "@/components/sections/Nav";
import { Hero } from "@/components/main/Hero";
import { TrustBand } from "@/components/main/TrustBand";
import { CapabilityStack } from "@/components/main/CapabilityStack";
import { StatsBand } from "@/components/main/StatsBand";
import { ProcessFlow } from "@/components/main/ProcessFlow";
import { AIDeepDive } from "@/components/main/AIDeepDive";
import { BenefitsList } from "@/components/main/BenefitsList";
import { PayerMarquee } from "@/components/sections/PayerMarquee";
import { FoundingMembers } from "@/components/main/FoundingMembers";
import { FinalCta } from "@/components/main/FinalCta";
import { Footer } from "@/components/sections/Footer";

export default function Home() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <TrustBand />
        <CapabilityStack />
        <StatsBand />
        <ProcessFlow />
        <AIDeepDive />
        <BenefitsList />
        <PayerMarquee />
        <FoundingMembers />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
