import { TrendingUp, BarChart3, FileText } from "lucide-react";

const pillars = [
    {
        icon: TrendingUp,
        title: "Continuous Context",
        description: "Track movement patterns between appointments, not just during visits. Get the full picture of your progress over time.",
    },
    {
        icon: BarChart3,
        title: "Clear Trends",
        description: "Simple, understandable insights—not confusing charts. See whether you're improving, stable, or need attention.",
    },
    {
        icon: FileText,
        title: "Clinician-Ready Report",
        description: "Deep reports designed for clinical review. Your care team gets the context they need in seconds.",
    },
];

export function ValuePillars() {
    return (
        <section className="py-24 relative">
            <div className="container mx-auto px-6">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-semibold mb-4">
                        Why track with <span className="text-gradient-primary">NMove</span>?
                    </h2>
                    <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                        Get the context you need between clinical visits, without the complexity.
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
