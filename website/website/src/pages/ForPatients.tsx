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
    Activity,
    Heart,
    Users,
    Calendar,
    CheckCircle,
    XCircle,
    Clock,
    ArrowRight,
} from "lucide-react";

const whoItHelps = [
    {
        icon: Activity,
        title: "Recovering from injury",
        description: "Track your rehab progress and share it with your physical therapist",
    },
    {
        icon: Heart,
        title: "Managing recurring pain",
        description: "Identify patterns and triggers in your movement over time",
    },
    {
        icon: Users,
        title: "Post-surgery monitoring",
        description: "Document your recovery journey with objective data",
    },
    {
        icon: Calendar,
        title: "Prevention-minded",
        description: "Stay ahead of potential issues with regular movement tracking",
    },
];

const whatItDoes = [
    "Tracks your gait patterns during everyday activities",
    "Shows trends over days, weeks, and months",
    "Highlights meaningful changes worth discussing",
    "Lets you add notes about pain, activities, and context",
];

const whatItDoesnt = [
    "Diagnose medical conditions",
    "Prescribe treatments or exercises",
    "Replace your doctor or physical therapist",
    "Provide real-time alerts or emergency monitoring",
    "Make clinical decisions for you",
];

const faqs = [
    {
        question: "Is NMove a medical device?",
        answer: "No. NMove is a wellness and tracking tool, not a medical device. It tracks movement patterns to help you and your care team have better conversations about your progress. It does not diagnose, treat, or prescribe.",
    },
    {
        question: "How long do I need to wear the sensor each day?",
        answer: "For best results, wear the sensor during your normal daily activities—typically 4-8 hours. The more you wear it, the better your trends will be. You don't need to do anything special; just go about your day.",
    },
    {
        question: "Will my insurance cover NMove?",
        answer: "Currently, NMove is not covered by insurance. We're a direct-to-consumer product. However, we're exploring partnerships with healthcare systems for potential coverage in the future.",
    },
    {
        question: "How accurate is the data?",
        answer: "NMove uses research-grade sensors similar to those used in clinical gait labs. While not intended for diagnosis, the data is reliable enough to track trends and support meaningful conversations with your care team.",
    },
    {
        question: "Can I share my data with my doctor?",
        answer: "Yes! You can generate a One-File Report report anytime and share it via email or print. The report is designed to be reviewed quickly, so it won't take up your doctor's valuable time.",
    },
    {
        question: "What if I have multiple conditions affecting my gait?",
        answer: "NMove tracks overall movement patterns rather than specific conditions. This makes it useful for anyone with gait concerns, regardless of the underlying cause. Your clinician can interpret the trends in the context of your specific situation.",
    },
    {
        question: "Is there a mobile app?",
        answer: "Yes, NMove includes a smartphone app for iOS and Android."
    },
    {
        question: "What happens to my data if I cancel?",
        answer: "You can export all your data before canceling. We retain your data for 30 days after cancellation, then permanently delete it unless you request earlier deletion.",
    },
];

const ForPatients = () => {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm mb-6">
                            For Patients
                        </span>
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            Track your progress. <span className="text-gradient-primary">Share your story.</span>
                        </h1>
                        <p className="text-xl text-muted-foreground">
                            NMove helps you capture what happens between appointments, so your care team
                            gets the full picture of your movement journey.
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
                                            It clips to your ankle or shoe—takes about 10 seconds.
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
                                            <strong className="text-foreground">Optional:</strong> Open the app to add
                                            notes about your day—pain levels, activities, or anything relevant.
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
                    <h2 className="text-3xl font-semibold mb-4">Ready to track your progress?</h2>
                    <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
                        Join our waitlist for early access. Be among the first to try NMove.
                    </p>
                    <Link to="/contact">
                        <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                            Join Waitlist
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </Link>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default ForPatients;
