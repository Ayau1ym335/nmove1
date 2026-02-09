import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import {
    FileText,
    Clock,
    CheckCircle,
    XCircle,
    TrendingUp,
    AlertCircle,
    Stethoscope,
    ArrowRight,
    Eye,
    Shield,
} from "lucide-react";

const whatYouReceive = [
    {
        icon: FileText,
        title: "One-File Report",
        description: "Key metrics and trends condensed for 30-60 second review",
    },
    {
        icon: TrendingUp,
        title: "Trend Timeline",
        description: "Visual history showing changes over the reporting period",
    },
    {
        icon: AlertCircle,
        title: "Flagged Changes",
        description: "Meaningful deviations highlighted for your attention",
    },
    {
        icon: Eye,
        title: "Patient Context",
        description: "Notes and events the patient logged (pain, activities, etc.)",
    },
];

const whatWeWontAsk = [
    "Daily monitoring or login requirements",
    "New platform or software to learn",
    "Interpretation or clinical decisions",
    "Liability for patient outcomes",
    "Changes to your current workflow",
];

const ForClinicians = () => {
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        organization: "",
        specialty: "",
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
                            <Stethoscope className="h-4 w-4" />
                            For Clinicians
                        </span>
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            Reduce uncertainty <span className="text-gradient-primary">between visits</span>
                        </h1>
                        <p className="text-xl text-muted-foreground">
                            Get objective movement context without adding workflow burden.
                            Your patients share; you review in under a minute.
                        </p>
                    </div>
                </div>
            </section>

            {/* What You'll Receive */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-semibold mb-4">What you'll receive</h2>
                        <p className="text-lg text-muted-foreground">
                            A patient-generated report designed for quick clinical review
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
                        {whatYouReceive.map((item) => (
                            <div
                                key={item.title}
                                className="p-6 rounded-xl bg-card border border-border"
                            >
                                <div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center mb-4">
                                    <item.icon className="h-5 w-5 text-secondary" />
                                </div>
                                <h3 className="font-semibold mb-2">{item.title}</h3>
                                <p className="text-sm text-muted-foreground">{item.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Sample Report Preview */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="grid lg:grid-cols-2 gap-12 items-center max-w-5xl mx-auto">
                        <div>
                            <h2 className="text-3xl font-semibold mb-6">Sample clinician report</h2>
                            <p className="text-muted-foreground mb-6 leading-relaxed">
                                Our report gives you the context you need.
                                Key metrics, trend visualization, and patient-logged events—all in one view.
                            </p>
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Weekly symmetry and stability trends</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Step timing and cadence summary</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Flagged deviations with context</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    <span className="text-muted-foreground">Patient notes and pain logs</span>
                                </div>
                            </div>
                        </div>

                        {/* Report mockup */}
                        <div className="bg-card rounded-2xl border border-border p-8 aspect-[3/4]">
                            <div className="h-full flex flex-col">
                                <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
                                    <div className="flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                                            <div className="w-4 h-4 rounded-full bg-primary" />
                                        </div>
                                        <span className="font-semibold">NMove</span>
                                    </div>
                                    <span className="text-xs text-muted-foreground">Movement Report</span>
                                </div>

                                <div className="space-y-4 flex-1">
                                    <div className="p-4 rounded-lg bg-muted/50">
                                        <div className="text-xs text-muted-foreground mb-1">Overall Status</div>
                                        <div className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full bg-green-500" />
                                            <span className="font-medium">Improving</span>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="p-3 rounded-lg bg-muted/50">
                                            <div className="text-xs text-muted-foreground mb-1">Symmetry</div>
                                            <div className="font-semibold">92%</div>
                                        </div>
                                        <div className="p-3 rounded-lg bg-muted/50">
                                            <div className="text-xs text-muted-foreground mb-1">Stability</div>
                                            <div className="font-semibold">87%</div>
                                        </div>
                                        <div className="p-3 rounded-lg bg-muted/50">
                                            <div className="text-xs text-muted-foreground mb-1">Cadence</div>
                                            <div className="font-semibold">112 spm</div>
                                        </div>
                                        <div className="p-3 rounded-lg bg-muted/50">
                                            <div className="text-xs text-muted-foreground mb-1">Change</div>
                                            <div className="font-semibold text-green-500">+8%</div>
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-lg bg-muted/50">
                                        <div className="text-xs text-muted-foreground mb-2">Weekly Trend</div>
                                        <div className="h-16 flex items-end gap-1">
                                            {[40, 45, 50, 55, 60, 65, 70].map((h, i) => (
                                                <div
                                                    key={i}
                                                    className="flex-1 bg-primary/60 rounded-t"
                                                    style={{ height: `${h}%` }}
                                                />
                                            ))}
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                                        <div className="flex items-center gap-2 text-xs text-yellow-500 mb-1">
                                            <AlertCircle className="h-4 w-4" />
                                            <span>Patient Note</span>
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            "Mild discomfort on Tuesday after hiking"
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* What We Won't Ask */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-semibold mb-4">What we won't ask of you</h2>
                            <p className="text-lg text-muted-foreground">
                                No new burden. No new liability.
                            </p>
                        </div>

                        <div className="p-8 rounded-2xl bg-card border border-border">
                            <ul className="space-y-4">
                                {whatWeWontAsk.map((item, index) => (
                                    <li key={index} className="flex items-center gap-4">
                                        <XCircle className="h-5 w-5 text-red-500 shrink-0" />
                                        <span className="text-muted-foreground">{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* Advisory/Pilot Signup */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="text-center mb-8">
                            <h2 className="text-3xl font-semibold mb-4">Join our clinician network</h2>
                            <p className="text-lg text-muted-foreground">
                                Get a sample report template and join our advisory or pilot list
                            </p>
                        </div>

                        {submitted ? (
                            <div className="p-8 rounded-2xl bg-card border border-border text-center">
                                <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-4">
                                    <CheckCircle className="h-8 w-8 text-green-500" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">Thank you!</h3>
                                <p className="text-muted-foreground">
                                    We'll send you a sample report template and more information about our clinician program.
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
                                        <Label htmlFor="email">Email *</Label>
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
                                        <Label htmlFor="organization">Organization</Label>
                                        <Input
                                            id="organization"
                                            value={formData.organization}
                                            onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="specialty">Specialty</Label>
                                        <Input
                                            id="specialty"
                                            value={formData.specialty}
                                            onChange={(e) => setFormData({ ...formData, specialty: e.target.value })}
                                            placeholder="e.g., Physical Therapy, Orthopedics"
                                            className="bg-background"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2 mb-6">
                                    <Label htmlFor="message">Message (optional)</Label>
                                    <Textarea
                                        id="message"
                                        value={formData.message}
                                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                        placeholder="Tell us about your interest in NMove..."
                                        rows={4}
                                        className="bg-background"
                                    />
                                </div>
                                <Button type="submit" className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                                    Request Sample Report
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

export default ForClinicians;
