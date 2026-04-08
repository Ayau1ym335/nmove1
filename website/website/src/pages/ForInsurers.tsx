import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import {
    Building2,
    Brain,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    ArrowRight,
    BarChart3,

} from "lucide-react";

const valueProps = [
    {
        icon: Brain,
        title: "Biological Age Scoring",
        description: "Assign each policyholder a biological age score derived from gait biomarkers — a stronger predictor of health outcomes than chronological age alone.",
    },
    {
        icon: TrendingUp,
        title: "Risk Stratification",
        description: "Segment your portfolio by aging velocity and pathology risk. Identify high-risk individuals years before claims materialize.",
    },
    {
        icon: AlertTriangle,
        title: "Pathology Risk Flags",
        description: "Detect early signals of fall risk, neurodegeneration, and cardiovascular decline — enabling proactive intervention and cost containment.",
    },
    {
        icon: BarChart3,
        title: "Wellness Program ROI",
        description: "Track whether wellness incentives are actually slowing biological aging. Reward policyholders whose scores improve over time.",
    },
];



const ForInsurers = () => {
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        company: "",
        role: "",
        policyholders: "",
        message: "",
    });
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // TODO: Connect to backend API
        setSubmitted(true);
    };

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary/10 text-secondary text-sm mb-6">
                            <Building2 className="h-4 w-4" />
                            For Insurance Companies
                        </span>
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            Underwrite the future with{" "}
                            <span className="text-gradient-primary">biological age data</span>
                        </h1>
                        <p className="text-xl text-muted-foreground mb-8">
                            NMove gives insurers a non-invasive, scalable way to assess biological age,
                            aging velocity, and pathology risk — enriching underwriting models with
                            data that predicts claims before they happen.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <a href="#pilot-form">
                                <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                                    Request a Pilot Program
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </a>
                        </div>
                    </div>
                </div>
            </section>

            {/* Value Props */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-semibold mb-4">What NMove gives insurers</h2>
                        <p className="text-lg text-muted-foreground">
                            A new category of health data — derived from how people walk
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
                        {valueProps.map((item) => (
                            <div
                                key={item.title}
                                className="p-6 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors"
                            >
                                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                                    <item.icon className="h-5 w-5 text-primary" />
                                </div>
                                <h3 className="font-semibold mb-2">{item.title}</h3>
                                <p className="text-sm text-muted-foreground">{item.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Sample Report Mockup */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="grid lg:grid-cols-2 gap-12 items-center max-w-5xl mx-auto">
                        <div>
                            <h2 className="text-3xl font-semibold mb-6">Sample policyholder report</h2>
                            <p className="text-muted-foreground mb-6 leading-relaxed">
                                Each assessment delivers a structured risk profile — ready for
                                actuarial review or direct integration into your underwriting workflow.
                            </p>
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Biological age vs. chronological age delta</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Aging velocity index (fast / normal / slow ager)</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Top 3 pathology risk flags with confidence scores</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Longitudinal trend vs. prior assessment</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Composite risk tier (Low / Moderate / High / Critical)</span>
                                </div>
                            </div>
                        </div>

                        {/* Report mockup */}
                        <div className="bg-card rounded-2xl border border-border p-8">
                            <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                                        <div className="w-4 h-4 rounded-full bg-primary" />
                                    </div>
                                    <span className="font-semibold">NMove</span>
                                </div>
                                <span className="text-xs text-muted-foreground">Biological Age Report</span>
                            </div>

                            <div className="space-y-4">
                                <div className="p-4 rounded-lg bg-muted/50">
                                    <div className="text-xs text-muted-foreground mb-1">Biological Age</div>
                                    <div className="flex items-baseline gap-2">
                                        <span className="text-3xl font-bold text-primary">52</span>
                                        <span className="text-sm text-muted-foreground">vs. 61 chronological</span>
                                    </div>
                                    <div className="text-xs text-green-500 mt-1">▼ 9 years younger than calendar age</div>
                                </div>

                                <div className="grid grid-cols-2 gap-3">
                                    <div className="p-3 rounded-lg bg-muted/50">
                                        <div className="text-xs text-muted-foreground mb-1">Aging Velocity</div>
                                        <div className="font-semibold text-green-500">Slow Ager</div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-muted/50">
                                        <div className="text-xs text-muted-foreground mb-1">Risk Tier</div>
                                        <div className="font-semibold text-green-500">Low</div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-muted/50">
                                        <div className="text-xs text-muted-foreground mb-1">Fall Risk</div>
                                        <div className="font-semibold">4%</div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-muted/50">
                                        <div className="text-xs text-muted-foreground mb-1">Neuro Risk</div>
                                        <div className="font-semibold">7%</div>
                                    </div>
                                </div>

                                <div className="p-4 rounded-lg bg-muted/50">
                                    <div className="text-xs text-muted-foreground mb-2">Aging Trend (12 months)</div>
                                    <div className="h-12 flex items-end gap-1">
                                        {[55, 54, 54, 53, 53, 52, 52].map((h, i) => (
                                            <div
                                                key={i}
                                                className="flex-1 bg-primary/60 rounded-t"
                                                style={{ height: `${((60 - h) / 10) * 100}%` }}
                                            />
                                        ))}
                                    </div>
                                    <div className="text-xs text-green-500 mt-1">Biological age improving ↓</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>



            {/* Pilot Form */}
            <section id="pilot-form" className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="text-center mb-8">
                            <h2 className="text-3xl font-semibold mb-4">Request a pilot program</h2>
                            <p className="text-lg text-muted-foreground">
                                Let's explore how biological age data can work for your portfolio
                            </p>
                        </div>

                        {submitted ? (
                            <div className="p-8 rounded-2xl bg-card border border-border text-center">
                                <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-4">
                                    <CheckCircle className="h-8 w-8 text-green-500" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">Thank you!</h3>
                                <p className="text-muted-foreground">
                                    Our team will reach out within 1–2 business days to discuss your pilot program.
                                </p>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="p-8 rounded-2xl bg-card border border-border">
                                <div className="grid md:grid-cols-2 gap-6 mb-6">
                                    <div className="space-y-2">
                                        <Label htmlFor="name">Full Name *</Label>
                                        <Input
                                            id="name"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            required
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="email">Work Email *</Label>
                                        <Input
                                            id="email"
                                            type="email"
                                            value={formData.email}
                                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                            required
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="company">Insurance Company *</Label>
                                        <Input
                                            id="company"
                                            value={formData.company}
                                            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                                            required
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="role">Your Role</Label>
                                        <Input
                                            id="role"
                                            value={formData.role}
                                            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                            placeholder="e.g., Chief Actuary, Underwriting Director"
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2 md:col-span-2">
                                        <Label htmlFor="policyholders">Approximate Policyholder Count</Label>
                                        <Input
                                            id="policyholders"
                                            value={formData.policyholders}
                                            onChange={(e) => setFormData({ ...formData, policyholders: e.target.value })}
                                            placeholder="e.g., 50,000"
                                            className="bg-background"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2 mb-6">
                                    <Label htmlFor="message">What are you hoping to solve? (optional)</Label>
                                    <Textarea
                                        id="message"
                                        value={formData.message}
                                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                        placeholder="Tell us about your underwriting challenges or wellness program goals..."
                                        rows={4}
                                        className="bg-background"
                                    />
                                </div>
                                <Button type="submit" className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                                    Request Pilot Program
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </form>
                        )}
                    </div>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default ForInsurers;
