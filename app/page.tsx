// Solvere main marketing site — premium B2B treatment.
// Section flow:
//   Nav → Hero (Inter 700 sans) → TrustBand → SolvereDashboard (kanban
//   pipeline) → CapabilityStack → StatsBand → ProcessFlow → Comparison
//   (us vs DIY) → AIDeepDive (tabbed) → BenefitsList → PayerMarquee →
//   FoundingMembers → FinalCta → Footer
//
// Old V1 preserved at /v1.

import { Nav } from "@/components/sections/Nav";
import { Hero } from "@/components/main/Hero";
import { TrustBand } from "@/components/main/TrustBand";
import { SolvereDashboard } from "@/components/main/SolvereDashboard";
import { CapabilityStack } from "@/components/main/CapabilityStack";
import { StatsBand } from "@/components/main/StatsBand";
import { ProcessFlow } from "@/components/main/ProcessFlow";
import { Comparison } from "@/components/main/Comparison";
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
        <SolvereDashboard />
        <CapabilityStack />
        <StatsBand />
        <ProcessFlow />
        <Comparison />
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
