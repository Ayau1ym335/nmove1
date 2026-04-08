import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import {
    ArrowLeftRight,
    Activity,
    Timer,
    Ruler,
    TrendingUp,
    AlertCircle,
    CheckCircle,
    Calendar,
    StickyNote,
    FileText,
    Clock,
    Zap,
    Smartphone,
    Battery,
    Cloud,
    Lock,
} from "lucide-react";

const measurements = [
    {
        icon: ArrowLeftRight,
        name: "Symmetry & Phases",
        description: "How evenly and smoothly you walk",
    },
    {
        icon: Activity,
        name: "Stability",
        description: "Variability and consistency of your movements",
    },
    {
        icon: Timer,
        name: "Step Timing",
        description: "Cadence and rhythm of your walking",
    },
    {
        icon: Ruler,
        name: "Range of Motion",
        description: "Knee and ankle movement proxy",
    },
    {
        icon: TrendingUp,
        name: "Change Over Time",
        description: "How your patterns evolve week over week",
    },
    {
        icon: AlertCircle,
        name: "Flags",
        description: "Meaningful deviations worth discussing",
    },
];

const userFeatures = [
    {
        icon: CheckCircle,
        title: "Daily Status",
        description: "Quick view: improving, stable, or needs attention",
    },
    {
        icon: Calendar,
        title: "Weekly Trend Cards",
        description: "Simple summaries of your weekly progress",
    },
    {
        icon: StickyNote,
        title: "Notes & Events",
        description: "Log pain levels, activities, and context",
    },
];

const insurerFeatures = [
    {
        icon: FileText,
        title: "Biological Age Report",
        description: "Per-policyholder biological age vs. chronological age delta",
    },
    {
        icon: TrendingUp,
        title: "Portfolio Risk Scoring",
        description: "Aggregate aging velocity and risk tier across your policyholder base",
    },
    {
        icon: Zap,
        title: "API Integration",
        description: "Connect directly to your underwriting or wellness platform",
    },
];

const deviceFeatures = [
    {
        icon: Smartphone,
        title: "Simple App",
        description: "iOS and Android compatible",
    },
    {
        icon: Battery,
        title: "All-Day Battery",
        description: "Wear from morning to evening",
    },
    {
        icon: Cloud,
        title: "Automatic Sync",
        description: "Data syncs when you're near your phone",
    },
    {
        icon: Lock,
        title: "Your Data, Protected",
        description: "Encrypted and never sold",
    },
];

const Product = () => {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            What <span className="text-gradient-primary">NMove</span> delivers
                        </h1>
                        <p className="text-xl text-muted-foreground">
                            More than just steps.
                        </p>
                    </div>
                </div>
            </section>

            {/* What You Measure */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-semibold mb-4">What we measure</h2>
                        <p className="text-lg text-muted-foreground">Six key aspects of your gait</p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
                        {measurements.map((item) => (
                            <div
                                key={item.name}
                                className="p-6 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors"
                            >
                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                        <item.icon className="h-5 w-5 text-primary" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold mb-1">{item.name}</h3>
                                        <p className="text-sm text-muted-foreground">{item.description}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* What Users See */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="grid lg:grid-cols-2 gap-12 items-center">
                        <div>
                            <span className="text-sm text-primary font-medium">For Individuals</span>
                            <h2 className="text-3xl font-semibold mt-2 mb-6">What you'll see</h2>
                            <div className="space-y-6">
                                {userFeatures.map((feature) => (
                                    <div key={feature.title} className="flex items-start gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                            <feature.icon className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold mb-1">{feature.title}</h3>
                                            <p className="text-sm text-muted-foreground">{feature.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Dashboard mockup placeholder */}
                        <div className="bg-card rounded-2xl border border-border p-8 aspect-[4/3] flex items-center justify-center">
                            <div className="text-center">
                                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                                    <Activity className="h-8 w-8 text-primary" />
                                </div>
                                <p className="text-muted-foreground">Dashboard Preview</p>
                                <p className="text-sm text-muted-foreground/60">Coming soon</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* What Insurers Get */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="grid lg:grid-cols-2 gap-12 items-center">
                        {/* Report mockup placeholder */}
                        <div className="order-2 lg:order-1 bg-card rounded-2xl border border-border p-8 aspect-[3/4] flex items-center justify-center">
                            <div className="text-center">
                                <div className="w-16 h-16 rounded-full bg-secondary/10 flex items-center justify-center mx-auto mb-4">
                                    <FileText className="h-8 w-8 text-secondary" />
                                </div>
                                <p className="text-muted-foreground">Insurer Report</p>
                                <p className="text-sm text-muted-foreground/60">Portfolio risk overview</p>
                            </div>
                        </div>

                        <div className="order-1 lg:order-2">
                            <span className="text-sm text-secondary font-medium">For Insurers</span>
                            <h2 className="text-3xl font-semibold mt-2 mb-6">What insurers receive</h2>
                            <div className="space-y-6">
                                {insurerFeatures.map((feature) => (
                                    <div key={feature.title} className="flex items-start gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0">
                                            <feature.icon className="h-5 w-5 text-secondary" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold mb-1">{feature.title}</h3>
                                            <p className="text-sm text-muted-foreground">{feature.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-8">
                                <Link to="/for-insurers">
                                    <Button variant="outline" className="border-secondary/50 text-secondary hover:bg-secondary/10">
                                        See insurer details →
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Device & App */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-semibold mb-4">Device & app basics</h2>
                        <p className="text-lg text-muted-foreground">Simple hardware. Secure software.</p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
                        {deviceFeatures.map((feature) => (
                            <div
                                key={feature.title}
                                className="p-6 rounded-xl bg-card border border-border text-center"
                            >
                                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                                    <feature.icon className="h-6 w-6 text-primary" />
                                </div>
                                <h3 className="font-semibold mb-1">{feature.title}</h3>
                                <p className="text-sm text-muted-foreground">{feature.description}</p>
                            </div>
                        ))}
                    </div>

                    {/* Data handling info */}
                    <div className="mt-12 max-w-2xl mx-auto p-6 rounded-xl bg-card border border-border">
                        <div className="flex items-start gap-4">
                            <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center shrink-0">
                                <Lock className="h-5 w-5 text-green-500" />
                            </div>
                            <div>
                                <h3 className="font-semibold mb-2">How we handle your data</h3>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    Your movement data is encrypted and stored securely. We never sell your data to third parties.
                                    You control who sees your information—share reports only when you choose to.
                                    Data stays on your device until you sync, and cloud storage is optional.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-16">
                <div className="container mx-auto px-6 text-center">
                    <h2 className="text-3xl font-semibold mb-4">Ready to get started?</h2>
                    <p className="text-lg text-muted-foreground mb-8">Join the waitlist for early access</p>
                    <Link to="/contact">
                        <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                            Join Waitlist
                        </Button>
                    </Link>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default Product;
