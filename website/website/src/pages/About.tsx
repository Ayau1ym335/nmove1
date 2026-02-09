import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Target, Users, Calendar, ArrowRight, Mail, MapPin } from "lucide-react";

const milestones = [
    { year: "2024", event: "Concept development and initial research" },
    { year: "2024", event: "Prototype sensor development" },
    { year: "2026", event: "Beta program launch" },
    { year: "2026", event: "Public launch (anticipated)" },
];

const About = () => {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            {/* Hero */}
            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                            More than just <span className="text-gradient-primary">steps</span>
                        </h1>
                        <p className="text-xl text-muted-foreground">
                            We're building tools to bridge the gap between clinical visits,
                            giving patients and clinicians the context they need.
                        </p>
                    </div>
                </div>
            </section>

            {/* Mission */}
            <section className="py-16 bg-muted/30">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="flex items-start gap-6">
                            <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                                <Target className="h-7 w-7 text-primary" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-semibold mb-4">Our Mission</h2>
                                <p className="text-lg text-muted-foreground leading-relaxed">
                                    To empower individuals on their path to recovery by transforming the way
                                    gait rehabilitation is managed and monitored.
                                </p>
                                <p className="text-lg text-muted-foreground leading-relaxed mt-4">
                                    We aim to enhance the quality of life for people with mobility challenges,
                                    ensuring that every step they take is a step toward a healthier, more active,
                                    and independent future.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Team */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="flex items-start gap-6 mb-12">
                            <div className="w-14 h-14 rounded-xl bg-secondary/10 flex items-center justify-center shrink-0">
                                <Users className="h-7 w-7 text-secondary" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-semibold mb-4">Our Team</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    We're a small team passionate about using technology to improve
                                    healthcare experiences.
                                </p>
                            </div>
                        </div>
                        {/* Team Members */}
                        {/* Team Members */}
                        <div className="grid md:grid-cols-2 lg:grid-cols-2 gap-x-8 gap-y-10 mt-12 mb-12">
                            {/* Profile 1 */}
                            <div className="flex flex-col items-center text-center p-6 bg-card rounded-xl border border-border shadow-sm">
                                <img
                                    src="/public/ayau.jpeg"
                                    alt="Ayaulym Balginbaeva"
                                    className="w-24 h-24 rounded-full object-cover mb-4"
                                />
                                <h3 className="text-xl font-semibold text-foreground mb-1">
                                    Ayaulym Balginbaeva
                                </h3>
                                <p className="text-sm font-medium text-primary mb-3">
                                    Backend & AI
                                </p>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    Designs backend architecture and develops AI logic.
                                </p>
                            </div>

                            <div className="flex flex-col items-center text-center p-6 bg-card rounded-xl border border-border shadow-sm">
                                <img
                                    src="/public/dariya.jpeg"
                                    alt="Team Member 2"
                                    className="w-24 h-24 rounded-full object-cover mb-4"
                                />
                                <h3 className="text-xl font-semibold text-foreground mb-1">
                                    Dariya Bekbolat
                                </h3>
                                <p className="text-sm font-medium text-primary mb-3">
                                    Frontend & Business Advisor 
                                </p>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    Leads UI development and aligns product decisions with business goals.
                                </p>
                            </div>

                            <div className="flex flex-col items-center text-center p-6 bg-card rounded-xl border border-border shadow-sm">
                                <img
                                    src="/public/aigerym.jpeg"
                                    alt="Team Member 3"
                                    className="w-24 h-24 rounded-full object-cover mb-4"
                                />
                                <h3 className="text-xl font-semibold text-foreground mb-1">
                                    Aigerym Qumarbek
                                </h3>
                                <p className="text-sm font-medium text-primary mb-3">
                                    Hardware Lead 
                                </p>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    Designs, integrates, and validates hardware components of the system.
                                </p>
                            </div>

                            <div className="flex flex-col items-center text-center p-6 bg-card rounded-xl border border-border shadow-sm">
                                <img
                                    src="/team/member4.jpg"
                                    alt="Team Member 4"
                                    className="w-24 h-24 rounded-full object-cover mb-4"
                                />
                                <h3 className="text-xl font-semibold text-foreground mb-1">
                                    Nuraiym Qabdulla
                                </h3>
                                <p className="text-sm font-medium text-primary mb-3">
                                    Medical Advisor & Designer
                                </p>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    Ensures clinical validity while shaping medically grounded UX and visuals.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Contact Info */}
            <section className="py-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <h2 className="text-2xl font-semibold mb-8 text-center">Get in touch</h2>
                        <div className="grid md:grid-cols-2 gap-6">
                            <div className="p-6 rounded-xl bg-card border border-border flex items-start gap-4">
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
                            <div className="p-6 rounded-xl bg-card border border-border flex items-start gap-4">
                                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                    <MapPin className="h-5 w-5 text-primary" />
                                </div>
                                <div>
                                    <h3 className="font-semibold mb-1">Location</h3>
                                    <p className="text-muted-foreground">Astana, Kazakhstan</p>
                                </div>
                            </div>
                        </div>

                        <div className="text-center mt-8">
                            <Link to="/contact">
                                <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                                    Contact Us
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default About;
