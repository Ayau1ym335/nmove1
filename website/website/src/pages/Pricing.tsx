import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Check, ArrowRight } from "lucide-react";
import { useState } from "react";

const tiers = [
    {
        name: "Free",
        price: "$0",
        period: "",
        description: "Basic tracking to get started",
        features: [
            "Functional Risk Score (basic)",
            "Basic gait trend tracking",
            "7-day history",
            "Daily status indicator",
            "Mobile app access",
        ],
        cta: "Join Waitlist",
        popular: false,
        planId: null,
    },
    {
        name: "Plus",
        price: "$15",
        period: "/month",
        description: "Track and slow your movement aging",
        features: [
            "Everything in Free",
            "Unlimited history",
            "Movement Age Indicator",
            "Aging Speed Tracking",
            "Weekly trend reports",
            "Detailed health reports",
            "Notes & event logging",
            "Change detection",
        ],
        cta: "Join Waitlist",
        popular: true,
        planId: "plus",
    },
    {
        name: "Pro",
        price: "$30",
        period: "/month",
        description: "For longevity enthusiasts and proactive health optimizers",
        features: [
            "Everything in Plus",
            "AI Functional Risk Interpretation",
            "Pathology risk deep-dive reports",
            "Longevity coaching tips",
            "Priority support",
            "Early access to new features",
            "Custom health goal tracking",
        ],
        cta: "Join Waitlist",
        popular: false,
        planId: null,
    },
];

const Pricing = () => {
    const [loadingPlan, setLoadingPlan] = useState<string | null>(null);

    const handleSubscribe = async (planId: string | null) => {
        if (!planId) return;

        setLoadingPlan(planId);
        try {
            const response = await fetch("http://localhost:8000/api/create-checkout-session", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ plan: planId }),
            });

            if (!response.ok) {
                throw new Error("Failed to create checkout session");
            }

            const data = await response.json();
            window.location.href = data.checkout_url;
        } catch (error) {
            console.error("Error:", error);
            alert("Failed to start checkout. Please try again.");
            setLoadingPlan(null);
        }
    };

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm mb-6">
                            Launching Soon
                        </span>
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            Simple, transparent <span className="text-gradient-primary">pricing</span>
                        </h1>
                        <p className="text-xl text-muted-foreground">
                            Choose the plan that fits your needs. All plans include the NMove sensor.
                        </p>
                    </div>
                </div>
            </section>

            {/* Hardware Section */}
            <section className="py-8">
                <div className="container mx-auto px-6">
                    <div className="max-w-4xl mx-auto">
                        <div className="p-8 rounded-2xl bg-gradient-to-br from-card to-background border border-primary/20 shadow-lg relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-50">
                                <span className="text-9xl font-bold text-primary/5 select-none">N</span>
                            </div>

                            <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                                <div className="space-y-4 max-w-lg">
                                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                                        Required One-Time Purchase
                                    </div>
                                    <h2 className="text-3xl font-bold">NMove Sensor Kit</h2>
                                    <p className="text-muted-foreground text-lg">
                                        The advanced gait-tracking hardware that powers your recovery.
                                        Includes sensor, charging dock, straps, and travel case.
                                    </p>
                                    <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4">
                                        {[
                                            "Precision 9-axis sensor",
                                            "8-hour battery life",
                                            "For daily use",
                                            "Water resistant"
                                        ].map(feat => (
                                            <li key={feat} className="flex items-center gap-2 text-sm text-foreground/80">
                                                <Check className="h-4 w-4 text-primary" /> {feat}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <div className="flex flex-col items-center gap-4 min-w-[200px] text-center bg-background/50 p-6 rounded-xl border border-border">
                                    <div className="text-sm text-muted-foreground font-medium uppercase tracking-wider">Hardware</div>
                                    <div className="text-4xl font-bold text-foreground">$49</div>
                                    <div className="text-xs text-muted-foreground">One-time purchase</div>
                                    <Link to="/contact" className="w-full">
                                        <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                                            Pre-order
                                            <ArrowRight className="ml-2 h-4 w-4" />
                                        </Button>
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing Cards */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                        {tiers.map((tier) => (
                            <div
                                key={tier.name}
                                className={`relative p-8 rounded-2xl border ${tier.popular
                                    ? "bg-gradient-to-b from-primary/10 to-transparent border-primary/50"
                                    : "bg-card border-border"
                                    }`}
                            >
                                {tier.popular && (
                                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary text-primary-foreground text-xs font-medium">
                                        Most Popular
                                    </div>
                                )}

                                <div className="mb-6">
                                    <h3 className="text-xl font-semibold mb-2">{tier.name}</h3>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-4xl font-bold">{tier.price}</span>
                                        <span className="text-muted-foreground">{tier.period}</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground mt-2">{tier.description}</p>
                                </div>

                                <ul className="space-y-3 mb-8">
                                    {tier.features.map((feature) => (
                                        <li key={feature} className="flex items-start gap-3">
                                            <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                                            <span className="text-sm text-muted-foreground">{feature}</span>
                                        </li>
                                    ))}
                                </ul>

                                {tier.planId ? (
                                    <Button
                                        onClick={() => handleSubscribe(tier.planId)}
                                        disabled={loadingPlan === tier.planId}
                                        className={`w-full ${tier.popular
                                            ? "bg-primary text-primary-foreground hover:bg-primary/90"
                                            : "bg-muted text-foreground hover:bg-muted/80"
                                            }`}
                                    >
                                        {loadingPlan === tier.planId ? "Loading..." : tier.cta}
                                        <ArrowRight className="ml-2 h-4 w-4" />
                                    </Button>
                                ) : (
                                    <Link to="/contact">
                                        <Button
                                            className={`w-full ${tier.popular
                                                ? "bg-primary text-primary-foreground hover:bg-primary/90"
                                                : "bg-muted text-foreground hover:bg-muted/80"
                                                }`}
                                        >
                                            {tier.cta}
                                            <ArrowRight className="ml-2 h-4 w-4" />
                                        </Button>
                                    </Link>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Early Access Note */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="max-w-2xl mx-auto text-center">
                        <h2 className="text-2xl font-semibold mb-4">Join for early access pricing</h2>
                        <p className="text-muted-foreground mb-6">
                            Waitlist members get exclusive early access pricing and priority for our
                            limited beta launch. Prices shown are estimates and may change.
                        </p>
                        <Link to="/contact">
                            <Button className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                                Join Waitlist
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* FAQ Preview */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <h2 className="text-2xl font-semibold mb-8 text-center">Common questions</h2>
                        <div className="space-y-6">
                            <div className="p-6 rounded-xl bg-card border border-border">
                                <h3 className="font-semibold mb-2">Is the sensor included?</h3>
                                <p className="text-sm text-muted-foreground">
                                    Yes! All plans include one NMove sensor. Additional sensors are available for purchase.
                                </p>
                            </div>
                            <div className="p-6 rounded-xl bg-card border border-border">
                                <h3 className="font-semibold mb-2">Can I cancel anytime?</h3>
                                <p className="text-sm text-muted-foreground">
                                    Absolutely. Cancel anytime with no fees. You keep your data and can export it before canceling.
                                </p>
                            </div>
                            <div className="p-6 rounded-xl bg-card border border-border">
                                <h3 className="font-semibold mb-2">Is there a free trial?</h3>
                                <p className="text-sm text-muted-foreground">
                                    The Free tier is free forever. For Plus, we offer a 14-day trial so you can experience full features.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default Pricing;
