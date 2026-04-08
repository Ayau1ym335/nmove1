import { GaitVisualization } from "./GaitVisualization";
import { Button } from "@/components/ui/button";
import { ArrowRight, Brain } from "lucide-react";
import { Link } from "react-router-dom";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-radial opacity-50" />

      {/* Subtle grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(hsl(var(--primary)) 1px, transparent 1px),
                           linear-gradient(90deg, hsl(var(--primary)) 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }}
      />

      <div className="container mx-auto px-6 pt-24 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Copy */}
          <div className="space-y-8">
            <div
              className="opacity-0 animate-fade-in"
              style={{ animationDelay: '0.1s' }}
            >
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-muted border border-border text-sm text-muted-foreground">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                Gait-based biological age analysis
              </span>
            </div>

            <h1
              className="text-4xl md:text-5xl lg:text-6xl font-semibold leading-tight opacity-0 animate-fade-in"
              style={{ animationDelay: '0.2s' }}
            >
              Move Your Age.{" "}
              <span className="text-gradient-primary">Know Your Risk.</span>
            </h1>

            <p
              className="text-lg md:text-xl text-muted-foreground max-w-xl leading-relaxed opacity-0 animate-fade-in"
              style={{ animationDelay: '0.3s' }}
            >
              NMove analyzes walking patterns to determine biological age, measure
              aging velocity, and predict pathology risk — giving insurers and
              individuals a powerful new lens on long-term health.
            </p>

            <div
              className="flex flex-col sm:flex-row gap-4 opacity-0 animate-fade-in"
              style={{ animationDelay: '0.4s' }}
            >
              <Link to="/contact">
                <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                  Request a Demo
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link to="/for-insurers">
                <Button variant="ghost" size="lg" className="text-muted-foreground hover:text-foreground">
                  <Brain className="mr-2 h-4 w-4" />
                  For Insurers
                </Button>
              </Link>
            </div>

            {/* Trust indicators */}
            <div
              className="flex flex-wrap items-center gap-6 pt-4 opacity-0 animate-fade-in"
              style={{ animationDelay: '0.5s' }}
            >
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                Science-backed biomarkers
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                Non-invasive assessment
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                Actuarially relevant
              </div>
            </div>
          </div>

          {/* Right: 3D Visualization */}
          <div
            className="h-[500px] lg:h-[600px] opacity-0 animate-scale-in"
            style={{ animationDelay: '0.3s' }}
          >
            <GaitVisualization />
          </div>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
    </section>
  );
}
