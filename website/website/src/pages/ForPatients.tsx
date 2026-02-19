import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import {
    Brain,
    TrendingUp,
    AlertTriangle,
    Dna,
    CheckCircle,
    XCircle,
    Clock,
    ArrowRight,
} from "lucide-react";

const whoItHelps = [
    {
        icon: Brain,
        title: "Longevity-focused individuals",
        description: "Track your biological age and see how lifestyle choices affect your aging trajectory",
    },
    {
        icon: Dna,
        title: "Family history of age-related disease",
        description: "Get early visibility into your personal risk profile before symptoms appear",
    },
    {
        icon: TrendingUp,
        title: "Health optimization enthusiasts",
        description: "Measure whether your diet, exercise, and sleep habits are actually slowing your aging",
    },
    {
        icon: AlertTriangle,
        title: "Prevention-minded adults",
        description: "Identify pathology risk factors years in advance and take targeted action",
    },
];

const whatItDoes = [
    "Determines your biological age from gait patterns",
    "Measures your aging velocity (fast, normal, or slow ager)",
    "Scores your risk for falls, neurodegeneration, and cardiovascular decline",
    "Tracks changes in biological age over time",
    "Provides a personal longevity dashboard",
];

const whatItDoesnt = [
    "Diagnose medical conditions",
    "Prescribe treatments or exercises",
    "Replace your doctor or specialist",
    "Provide real-time emergency monitoring",
    "Make clinical decisions for you",
];

const faqs = [
    {
        question: "What is biological age and how is it different from chronological age?",
        answer: "Chronological age is simply how many years you've been alive. Biological age reflects how old your body actually functions — based on measurable biomarkers. Someone who is 60 chronologically might have a biological age of 50 (aging well) or 70 (aging faster than expected). NMove derives biological age from gait patterns, which are among the most powerful predictors of physiological aging.",
    },
    {
        question: "How accurate is the biological age score?",
        answer: "NMove uses research-grade sensors and AI models trained on large longitudinal datasets. The biological age score is validated against established aging biomarkers and health outcomes. While not a medical diagnosis, it provides a reliable and reproducible measure of functional aging.",
    },
    {
        question: "What does 'aging velocity' mean?",
        answer: "Aging velocity measures how fast or slow you are aging relative to your peers. A 'slow ager' is someone whose biological age is improving or staying stable over time. A 'fast ager' is someone whose biological age is increasing faster than their chronological age. Tracking velocity over time is more actionable than a single snapshot score.",
    },
    {
        question: "What pathology risks does NMove detect?",
        answer: "NMove's gait analysis can flag early risk signals for falls and balance disorders, neurodegenerative conditions (such as early Parkinson's patterns), cardiovascular health markers, and musculoskeletal decline. These are risk indicators, not diagnoses — always consult a healthcare professional for medical decisions.",
    },
    {
        question: "How long do I need to wear the sensor?",
        answer: "For best results, wear the sensor during normal daily activities — typically 4–8 hours. The more data captured, the more accurate your biological age score. You don't need to do anything special; just go about your day.",
    },
    {
        question: "Can I improve my biological age score?",
        answer: "Yes. Biological age is not fixed. Regular exercise, quality sleep, stress management, and good nutrition have all been shown to slow biological aging. NMove lets you track whether your lifestyle interventions are actually working — giving you objective feedback over time.",
    },
    {
        question: "Is there a mobile app?",
        answer: "Yes, NMove includes a smartphone app for iOS and Android where you can view your biological age score, aging velocity trend, and risk profile.",
    },
    {
        question: "What happens to my data if I cancel?",
        answer: "You can export all your data before canceling. We retain your data for 30 days after cancellation, then permanently delete it unless you request earlier deletion.",
    },
];

const ForIndividuals = () => {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm mb-6">
                            For Individuals
                        </span>
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            Discover your biological age.{" "}
                            <span className="text-gradient-primary">Move your age.</span>
                        </h1>
                        <p className="text-xl text-muted-foreground">
                            NMove analyzes your walking patterns to reveal your biological age,
                            aging velocity, and personal pathology risk — giving you a powerful
                            new window into your long-term health.
                        </p>
                    </div>
                </div>
            </section>

            {/* Who It Helps */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-semibold mb-4">Who NMove helps</h2>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
                        {whoItHelps.map((item) => (
                            <div
                                key={item.title}
                                className="p-6 rounded-xl bg-card border border-border text-center"
                            >
                                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                                    <item.icon className="h-6 w-6 text-primary" />
                                </div>
                                <h3 className="font-semibold mb-2">{item.title}</h3>
                                <p className="text-sm text-muted-foreground">{item.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* What It Does / Doesn't */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
                        {/* What it does */}
                        <div className="p-8 rounded-2xl bg-card border border-border">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                </div>
                                <h3 className="text-xl font-semibold">What NMove does</h3>
                            </div>
                            <ul className="space-y-4">
                                {whatItDoes.map((item, index) => (
                                    <li key={index} className="flex items-start gap-3">
                                        <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                                        <span className="text-muted-foreground">{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* What it doesn't */}
                        <div className="p-8 rounded-2xl bg-card border border-border">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                                    <XCircle className="h-5 w-5 text-red-500" />
                                </div>
                                <h3 className="text-xl font-semibold">What NMove doesn't do</h3>
                            </div>
                            <ul className="space-y-4">
                                {whatItDoesnt.map((item, index) => (
                                    <li key={index} className="flex items-start gap-3">
                                        <XCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                                        <span className="text-muted-foreground">{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* Daily Expectations */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-semibold mb-4">What you'll do daily</h2>
                            <p className="text-lg text-muted-foreground">
                                NMove fits into your life, not the other way around
                            </p>
                        </div>

                        <div className="p-8 rounded-2xl bg-card border border-border">
                            <div className="flex items-start gap-6">
                                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                                    <Clock className="h-6 w-6 text-primary" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-4">Simple daily routine</h3>
                                    <div className="space-y-4 text-muted-foreground">
                                        <p>
                                            <strong className="text-foreground">Morning:</strong> Put on your NMove sensor.
                                            It clips to your ankle or shoe — takes about 10 seconds.
                                        </p>
                                        <p>
                                            <strong className="text-foreground">During the day:</strong> Just live your life.
                                            Walk to work, run errands, exercise. NMove captures it all automatically.
                                        </p>
                                        <p>
                                            <strong className="text-foreground">Evening:</strong> Take off the sensor and
                                            place it on the charger. Your data syncs automatically.
                                        </p>
                                        <p>
                                            <strong className="text-foreground">In the app:</strong> View your biological age
                                            score, aging velocity trend, and top risk flags — updated daily.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* FAQ */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-semibold mb-4">Frequently asked questions</h2>
                        </div>

                        <Accordion type="single" collapsible className="space-y-4">
                            {faqs.map((faq, index) => (
                                <AccordionItem
                                    key={index}
                                    value={`item-${index}`}
                                    className="bg-card border border-border rounded-xl px-6"
                                >
                                    <AccordionTrigger className="text-left hover:no-underline py-5">
                                        <span className="font-medium">{faq.question}</span>
                                    </AccordionTrigger>
                                    <AccordionContent className="text-muted-foreground pb-5">
                                        {faq.answer}
                                    </AccordionContent>
                                </AccordionItem>
                            ))}
                        </Accordion>
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6 text-center">
                    <h2 className="text-3xl font-semibold mb-4">Ready to discover your biological age?</h2>
                    <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
                        Join our early access list. Be among the first to move your age.
                    </p>
                    <Link to="/contact">
                        <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                            Join Early Access
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </Link>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default ForIndividuals;
