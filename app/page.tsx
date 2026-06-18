import Nav from "@/components/Nav";
import Hero from "@/components/Hero";
import TrustBand from "@/components/TrustBand";
import SolvereDashboard from "@/components/SolvereDashboard";
import CapabilityStack from "@/components/CapabilityStack";
import StatsBand from "@/components/StatsBand";
import Comparison from "@/components/Comparison";
import AIDeepDive from "@/components/AIDeepDive";
import BenefitsList from "@/components/BenefitsList";
import PayerMarquee from "@/components/PayerMarquee";
import FoundingMembers from "@/components/FoundingMembers";
import FinalCta from "@/components/FinalCta";
import Footer from "@/components/Footer";

export default function Page() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <TrustBand />
        <SolvereDashboard />
        <CapabilityStack />
        <StatsBand />
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
