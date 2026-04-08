import { BarChart3, Scan, TrendingUp } from "lucide-react";

const pillars = [
    {
        icon: BarChart3,
        title: "Actuarially Relevant Data",
        description: "Gait biomarkers that correlate with long-term health costs, mortality risk, and claims frequency — enriching your underwriting models.",
    },
    {
        icon: Scan,
        title: "Non-Invasive Assessment",
        description: "No blood draws, no clinical visits. A wearable sensor captures everything needed to compute biological age and risk scores.",
    },
    {
        icon: TrendingUp,
        title: "Longitudinal Risk Tracking",
        description: "Monitor policyholders' aging trajectory over time. Detect deterioration early and reward those who are aging well.",
    },
];

export function ValuePillars() {
    return (
        <section className="py-24 relative">
            <div className="container mx-auto px-6">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-semibold mb-4">
                        Why insurers choose <span className="text-gradient-primary">NMove</span>
                    </h2>
                    <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                        A new category of health data — derived from how people walk, not what they report.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8">
                    {pillars.map((pillar, index) => (
                        <div
                            key={pillar.title}
                            className="group p-8 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all duration-300"
                            style={{ animationDelay: `${index * 0.1}s` }}
                        >
                            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                                <pillar.icon className="h-7 w-7 text-primary" />
                            </div>
                            <h3 className="text-xl font-semibold mb-3">{pillar.title}</h3>
                            <p className="text-muted-foreground leading-relaxed">{pillar.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
