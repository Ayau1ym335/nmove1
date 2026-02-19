import { Navbar } from "@/components/Navbar";
import { HeroSection } from "@/components/HeroSection";
import { ValuePillars } from "@/components/ValuePillars";
import { HowItWorksSection } from "@/components/HowItWorksSection";

import { FAQTeaser } from "@/components/FAQTeaser";
import { CTASection } from "@/components/CTASection";
import { Footer } from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <HeroSection />
      <ValuePillars />
      <HowItWorksSection />

      <FAQTeaser />
      <CTASection />
      <Footer />
    </div>
  );
};

export default Index;
