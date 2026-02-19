import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState, useEffect } from "react";
import { VideoIntro } from "@/components/VideoIntro";

// Pages
import Index from "@/pages/Index";
import Product from "@/pages/Product";
import ForPatients from "@/pages/ForPatients";
import ForInsurers from "@/pages/ForInsurers";
import ForEmployers from "@/pages/ForEmployers";
import ForClinicians from "@/pages/ForClinicians";
import Pricing from "@/pages/Pricing";
import About from "@/pages/About";
import Blog from "@/pages/Blog";
import BlogPost from "@/pages/BlogPost";
import Contact from "@/pages/Contact";
import PrivacyPolicy from "@/pages/PrivacyPolicy";
import Terms from "@/pages/Terms";
import MedicalDisclaimer from "@/pages/MedicalDisclaimer";
import Success from "@/pages/Success";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  const [showIntro, setShowIntro] = useState(false);

  useEffect(() => {
    const hasSeenIntro = sessionStorage.getItem("hasSeenIntro");
    if (!hasSeenIntro) {
      setShowIntro(true);
    }
  }, []);

  const handleIntroComplete = () => {
    sessionStorage.setItem("hasSeenIntro", "true");
    setShowIntro(false);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        {showIntro && (
          <VideoIntro
            videoSrc="/intro.mp4"
            onComplete={handleIntroComplete}
          />
        )}
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/product" element={<Product />} />
            <Route path="/for-individuals" element={<ForPatients />} />
            <Route path="/for-patients" element={<ForPatients />} />
            <Route path="/for-insurers" element={<ForInsurers />} />
            <Route path="/for-employers" element={<ForEmployers />} />
            <Route path="/for-clinicians" element={<ForClinicians />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/about" element={<About />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/:slug" element={<BlogPost />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/medical-disclaimer" element={<MedicalDisclaimer />} />
            <Route path="/success" element={<Success />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;

