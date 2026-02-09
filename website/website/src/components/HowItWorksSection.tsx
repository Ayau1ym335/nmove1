import { Watch, Footprints, TrendingUp, Share2 } from "lucide-react";

const steps = [
  {
    icon: Watch,
    step: "1",
    title: "Wear",
    description: "Put on your NMove sensor—it's lightweight and comfortable for all-day wear.",
  },
  {
    icon: Footprints,
    step: "2",
    title: "Walk Normally",
    description: "Go about your day. The sensor captures movement data during everyday activities.",
  },
  {
    icon: TrendingUp,
    step: "3",
    title: "Trends Update",
    description: "Your dashboard updates with daily and weekly trends. See your progress at a glance.",
  },
  {
    icon: Share2,
    step: "4",
    title: "Share Report",
    description: "Generate a deep report for your clinician before your next visit.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 bg-muted/30">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-semibold mb-4">
            How it <span className="text-gradient-primary">works</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            4 simple steps to better movement insights
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <div key={step.title} className="relative group">
              {/* Connection line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-12 left-1/2 w-full h-0.5 bg-border group-hover:bg-primary/30 transition-colors" />
              )}

              <div className="relative z-10 text-center">
                <div className="w-24 h-24 rounded-2xl bg-card border border-border mx-auto mb-6 flex items-center justify-center group-hover:border-primary/50 transition-colors">
                  <step.icon className="h-10 w-10 text-primary" />
                </div>
                <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center mx-auto mb-4">
                  {step.step}
                </div>
                <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
