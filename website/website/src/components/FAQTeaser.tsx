import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const faqs = [
    {
        question: "Is NMove a medical device?",
        answer: "No. NMove is a wellness tool that tracks movement patterns. It does not diagnose, treat, or prescribe. Always consult with your healthcare provider for medical advice.",
    },
    {
        question: "How does NMove determine biological age?",
        answer: "NMove uses research-grade gait sensors to capture dozens of movement biomarkers. Our AI models analyze these patterns against validated aging datasets to produce your biological age score — a stronger health predictor than chronological age alone.",
    },
    {
        question: "What do I need to use NMove?",
        answer: "You'll need the NMove sensor (included with your subscription) and a smartphone with the NMove app. The sensor is lightweight and designed for comfortable all-day wear.",
    },
    {
        question: "How accurate is the data?",
        answer: "Gait-related metrics are designed to be directionally reliable, meaning they are most accurate for tracking changes and trends over time",
    },
];

export function FAQTeaser() {
    return (
        <section className="py-24 bg-muted/30">
            <div className="container mx-auto px-6">
                <div className="max-w-3xl mx-auto">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl md:text-4xl font-semibold mb-4">
                            Common <span className="text-gradient-primary">Questions</span>
                        </h2>
                        <p className="text-lg text-muted-foreground">
                            Quick answers to help you understand NMove
                        </p>
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

                    <div className="text-center mt-8">
                        <Link to="/for-individuals">
                            <Button variant="ghost" className="text-primary hover:text-primary/80">
                                View all FAQs →
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </section>
    );
}
