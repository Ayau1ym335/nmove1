import { Brain, TrendingUp, AlertTriangle, Clock } from "lucide-react";

const capabilities = [
  {
    icon: Brain,
    title: "Biological Age Score",
    description: "Derive a person's functional biological age from gait biomarkers — independent of chronological age, revealing true physiological status."
  },
  {
    icon: TrendingUp,
    title: "Aging Velocity Index",
    description: "Measure how fast or slow an individual is aging relative to their peers. Detect accelerated aging years before clinical symptoms appear."
  },
  {
    icon: AlertTriangle,
    title: "Pathology Risk Prediction",
    description: "Predict risk of falls, neurodegeneration, cardiovascular events, and musculoskeletal decline from subtle gait pattern changes."
  },
  {
    icon: Clock,
    title: "Longitudinal Monitoring",
    description: "Track biological age and risk scores quarterly or annually. Identify policyholders whose risk profile is improving or deteriorating."
  }
];

export function CapabilitiesSection() {
  return (
    <section id="capabilities" className="py-24 relative bg-muted/30">
      <div className="container mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6">
              Objective data for{' '}
              <span className="text-gradient-primary">smarter underwriting</span>
            </h2>
            <p className="text-muted-foreground text-lg mb-8 leading-relaxed">
              Gait is one of the most powerful biomarkers of aging. NMove turns
              walking patterns into actuarially relevant risk scores — giving
              insurers a non-invasive, scalable window into long-term health.
            </p>

            <div className="bg-card border border-border rounded-xl p-6">
              <p className="text-sm text-muted-foreground italic">
                "The biological age data from NMove has transformed how we think about
                risk stratification. We're seeing correlations with claims that no
                traditional underwriting metric could capture."
              </p>
              <div className="mt-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <span className="text-primary text-sm font-medium">AK</span>
                </div>
                <div>
                  <div className="text-sm font-medium">Chief Actuary</div>
                  <div className="text-xs text-muted-foreground">Life & Health Insurance Group</div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            {capabilities.map((capability, index) => (
              <div
                key={index}
                className="bg-card border border-border rounded-xl p-6 hover:border-primary/30 transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <capability.icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-medium mb-2">{capability.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {capability.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
