import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useState } from "react";
import { CheckCircle, Mail, MapPin, ArrowRight } from "lucide-react";

const Contact = () => {
    const [formType, setFormType] = useState<"individual" | "insurer">("individual");
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        organization: "",
        message: "",
    });
    const [submitted, setSubmitted] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError("");

        try {
            const response = await fetch("http://localhost:8000/api/contact", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name: formData.name,
                    email: formData.email,
                    form_type: formType,
                    message: formData.message,
                    organization: formData.organization,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to submit form");
            }

            setSubmitted(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to submit. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            Get in <span className="text-gradient-primary">touch</span>
                        </h1>
                        <p className="text-xl text-muted-foreground">
                            Join our waitlist for early access, or reach out with questions.
                        </p>
                    </div>
                </div>
            </section>

            {/* Contact Form */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="grid lg:grid-cols-2 gap-12 max-w-5xl mx-auto">
                        {/* Form */}
                        <div>
                            {submitted ? (
                                <div className="p-8 rounded-2xl bg-card border border-border text-center">
                                    <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-4">
                                        <CheckCircle className="h-8 w-8 text-green-500" />
                                    </div>
                                    <h3 className="text-xl font-semibold mb-2">Thank you!</h3>
                                    <p className="text-muted-foreground">
                                        {formType === "individual"
                                            ? "You're on the waitlist! We'll be in touch when early access opens."
                                            : "Our team will reach out within 1–2 business days to discuss a pilot program."}
                                    </p>
                                </div>
                            ) : (
                                <form onSubmit={handleSubmit} className="p-8 rounded-2xl bg-card border border-border">
                                    <h2 className="text-2xl font-semibold mb-6">I am a...</h2>

                                    <RadioGroup
                                        value={formType}
                                        onValueChange={(value) => setFormType(value as "individual" | "insurer")}
                                        className="flex gap-4 mb-8"
                                    >
                                        <div className="flex items-center space-x-2">
                                            <RadioGroupItem value="individual" id="individual" />
                                            <Label htmlFor="individual" className="cursor-pointer">Individual</Label>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <RadioGroupItem value="insurer" id="insurer" />
                                            <Label htmlFor="insurer" className="cursor-pointer">Insurer / Business</Label>
                                        </div>
                                    </RadioGroup>

                                    <div className="space-y-6">
                                        <div className="grid md:grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="name">Name {formType === "insurer" && "*"}</Label>
                                                <Input
                                                    id="name"
                                                    value={formData.name}
                                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                                    required={formType === "insurer"}
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
                                        </div>

                                        {formType === "insurer" && (
                                            <div className="space-y-2">
                                                <Label htmlFor="organization">Insurance Company / Organization</Label>
                                                <Input
                                                    id="organization"
                                                    value={formData.organization}
                                                    onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                                                    className="bg-background"
                                                />
                                            </div>
                                        )}

                                        <div className="space-y-2">
                                            <Label htmlFor="message">Message (optional)</Label>
                                            <Textarea
                                                id="message"
                                                value={formData.message}
                                                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                                placeholder={
                                                    formType === "individual"
                                                        ? "Tell us about your interest in NMove..."
                                                        : "Tell us about your organization and interest in biological age data..."
                                                }
                                                rows={4}
                                                className="bg-background"
                                            />
                                        </div>

                                        <div className="text-xs text-muted-foreground">
                                            By submitting, you agree to our{" "}
                                            <a href="/privacy" className="text-primary hover:underline">Privacy Policy</a>
                                            {" "}and{" "}
                                            <a href="/terms" className="text-primary hover:underline">Terms of Service</a>.
                                        </div>

                                        {error && (
                                            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/50 text-red-500 text-sm">
                                                {error}
                                            </div>
                                        )}

                                        <Button
                                            type="submit"
                                            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                                            disabled={isSubmitting}
                                        >
                                            {isSubmitting ? "Sending..." : (formType === "individual" ? "Join Waitlist" : "Request Pilot Program")}
                                            <ArrowRight className="ml-2 h-4 w-4" />
                                        </Button>
                                    </div>
                                </form>
                            )}
                        </div>

                        {/* Contact Info */}
                        <div className="space-y-8">
                            <div>
                                <h2 className="text-2xl font-semibold mb-6">Contact information</h2>
                                <div className="space-y-6">
                                    <div className="flex items-start gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                            <Mail className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold mb-1">Email</h3>
                                            <a href="mailto:nmove.co@gmail.com" className="text-muted-foreground hover:text-primary transition-colors">
                                                nmove.co@gmail.com
                                            </a>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                            <MapPin className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold mb-1">Location</h3>
                                            <p className="text-muted-foreground">Astana, Kazakhstan</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="p-6 rounded-xl bg-muted/50 border border-border">
                                <h3 className="font-semibold mb-3">Response time</h3>
                                <p className="text-sm text-muted-foreground">
                                    We typically respond within 1-2 business days. For urgent inquiries,
                                    please mention "URGENT" in your message.
                                </p>
                            </div>

                            <div className="p-6 rounded-xl bg-gradient-to-br from-primary/10 to-secondary/10 border border-primary/20">
                                <h3 className="font-semibold mb-3">For insurers</h3>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Looking to enrich your underwriting models with biological age data?
                                    Let's explore a pilot program for your portfolio.
                                </p>
                                <a href="/for-insurers" className="text-primary text-sm hover:underline">
                                    Learn more about insurer solutions →
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default Contact;
