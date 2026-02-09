import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { AlertTriangle } from "lucide-react";

const MedicalDisclaimer = () => {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 rounded-xl bg-yellow-500/10 flex items-center justify-center">
                                <AlertTriangle className="h-6 w-6 text-yellow-500" />
                            </div>
                            <h1 className="text-4xl font-semibold">Medical Disclaimer</h1>
                        </div>
                        <p className="text-muted-foreground mb-8">Last updated: February 2026</p>

                        <div className="prose prose-invert max-w-none space-y-8">
                            <section className="p-6 rounded-2xl bg-yellow-500/10 border border-yellow-500/20">
                                <h2 className="text-xl font-semibold text-yellow-500 mb-4">Important Notice</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    NMove is <strong className="text-foreground">NOT a medical device</strong> and is
                                    intended for <strong className="text-foreground">general wellness purposes only</strong>.
                                    The information provided by NMove's services should not be considered medical advice,
                                    diagnosis, or treatment.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">What NMove Is</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    NMove is a consumer wellness product that tracks movement patterns and provides
                                    trend information. It is designed to:
                                </p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground mt-4">
                                    <li>Track gait metrics over time for personal awareness</li>
                                    <li>Generate trend summaries that may be shared with healthcare providers</li>
                                    <li>Provide general wellness information about movement patterns</li>
                                    <li>Support (not replace) conversations with healthcare professionals</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">What NMove Is NOT</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    NMove is NOT:
                                </p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground mt-4">
                                    <li><strong className="text-foreground">A medical device</strong> – It is not FDA-cleared or approved for medical use</li>
                                    <li><strong className="text-foreground">Diagnostic</strong> – It cannot diagnose any medical condition</li>
                                    <li><strong className="text-foreground">Prescriptive</strong> – It does not recommend treatments, medications, or therapies</li>
                                    <li><strong className="text-foreground">A replacement for clinical care</strong> – It cannot replace professional medical evaluation</li>
                                    <li><strong className="text-foreground">Emergency monitoring</strong> – It should not be used for fall detection or emergency alerts</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Consult Your Healthcare Provider</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    <strong className="text-foreground">Always consult with a qualified healthcare professional</strong> regarding
                                    any questions or concerns about your health, medical conditions, or treatment options.
                                </p>
                                <p className="text-muted-foreground mt-4">
                                    NMove data should be considered supplemental information only. Any health-related
                                    decisions should be made in consultation with your physician, physical therapist,
                                    or other qualified healthcare provider.
                                </p>
                                <p className="text-muted-foreground mt-4">
                                    If you experience pain, discomfort, or any symptoms of concern, seek medical
                                    attention immediately. Do not delay seeking medical care based on information
                                    from NMove.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Data Accuracy Limitations</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    While we strive for accuracy, NMove's measurements are subject to limitations:
                                </p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground mt-4">
                                    <li>Sensor placement and fit may affect accuracy</li>
                                    <li>Environmental factors may impact readings</li>
                                    <li>Individual variations may not be captured</li>
                                    <li>Technical issues may result in incomplete or inaccurate data</li>
                                </ul>
                                <p className="text-muted-foreground mt-4">
                                    Data should be interpreted as general trends, not precise clinical measurements.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">For Healthcare Providers</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    If you are a healthcare provider reviewing NMove data shared by a patient:
                                </p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground mt-4">
                                    <li>This data is patient-generated and not clinically validated</li>
                                    <li>It should be considered supplemental context, not clinical evidence</li>
                                    <li>Clinical examination and professional judgment should take precedence</li>
                                    <li>NMove does not make treatment recommendations</li>
                                    <li>We do not assume liability for clinical decisions based on this data</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">No Medical Advice</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    The content provided through NMove's services, including the website, application,
                                    and reports, does not constitute medical advice. Any reliance you place on such
                                    information is strictly at your own risk.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Emergency Situations</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    <strong className="text-foreground">In case of a medical emergency, call your local emergency services
                                        immediately.</strong> NMove is not designed for emergency detection, fall alerting,
                                    or any time-critical health monitoring.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Questions</h2>
                                <p className="text-muted-foreground">
                                    If you have questions about this disclaimer:<br />
                                    Email: nmove.co@gmail.com
                                </p>
                            </section>
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default MedicalDisclaimer;
