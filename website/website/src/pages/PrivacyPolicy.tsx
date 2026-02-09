import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const PrivacyPolicy = () => {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <main className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        <h1 className="text-4xl font-semibold mb-4">Privacy Policy</h1>
                        <p className="text-muted-foreground mb-8">Last updated: February 2026</p>

                        <div className="prose prose-invert max-w-none space-y-8">
                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Overview</h2>
                                <p className="text-muted-foreground leading-relaxed">
                                    NMove ("we," "our," or "us") is committed to protecting your privacy.
                                    This Privacy Policy explains how we collect, use, disclose, and safeguard
                                    your information when you use our website, mobile application, and movement
                                    tracking services (collectively, the "Services").
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Information We Collect</h2>

                                <h3 className="text-lg font-semibold mb-2">Personal Information</h3>
                                <p className="text-muted-foreground mb-4">When you create an account or contact us, we may collect:</p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                    <li>Name and email address</li>
                                    <li>Account credentials</li>
                                    <li>Communication preferences</li>
                                    <li>Any information you provide in messages to us</li>
                                </ul>

                                <h3 className="text-lg font-semibold mt-6 mb-2">Movement Data</h3>
                                <p className="text-muted-foreground mb-4">When you use our sensor and app, we collect:</p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                    <li>Gait metrics (symmetry, stability, timing patterns)</li>
                                    <li>Movement session timestamps and duration</li>
                                    <li>User-entered notes (pain levels, activities, symptoms)</li>
                                    <li>Device usage patterns</li>
                                </ul>

                                <h3 className="text-lg font-semibold mt-6 mb-2">Technical Information</h3>
                                <p className="text-muted-foreground mb-4">We automatically collect:</p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                    <li>Device type, OS version, app version</li>
                                    <li>IP address and approximate location (country/region)</li>
                                    <li>Usage statistics and analytics</li>
                                    <li>Error logs and performance data</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">How We Use Your Information</h2>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                    <li><strong className="text-foreground">Provide Services:</strong> Process movement data, generate reports, and deliver app functionality</li>
                                    <li><strong className="text-foreground">Improve Services:</strong> Analyze usage patterns to enhance features and user experience</li>
                                    <li><strong className="text-foreground">Communicate:</strong> Send service updates, respond to inquiries, and provide support</li>
                                    <li><strong className="text-foreground">Research:</strong> Conduct aggregated, de-identified research to improve our algorithms (only with consent)</li>
                                    <li><strong className="text-foreground">Legal Compliance:</strong> Meet legal obligations and protect our rights</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Data Sharing</h2>
                                <p className="text-muted-foreground mb-4">
                                    <strong className="text-foreground">We do not sell your personal or movement data.</strong>
                                </p>
                                <p className="text-muted-foreground mb-4">We may share information with:</p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                    <li><strong className="text-foreground">Service Providers:</strong> Third parties who help us operate our services (hosting, analytics, email)</li>
                                    <li><strong className="text-foreground">Your Clinicians:</strong> Only when you explicitly choose to share a report</li>
                                    <li><strong className="text-foreground">Legal Requirements:</strong> When required by law or to protect safety</li>
                                    <li><strong className="text-foreground">Business Transfers:</strong> In connection with merger, acquisition, or sale of assets</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Your Rights</h2>
                                <p className="text-muted-foreground mb-4">You have the right to:</p>
                                <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                                    <li>Access your personal and movement data</li>
                                    <li>Export your data in a portable format</li>
                                    <li>Correct inaccurate information</li>
                                    <li>Delete your account and associated data</li>
                                    <li>Opt out of marketing communications</li>
                                </ul>
                                <p className="text-muted-foreground mt-4">
                                    To exercise these rights, contact us at nmove.co@gmail.com.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Changes to This Policy</h2>
                                <p className="text-muted-foreground">
                                    We may update this Privacy Policy from time to time. Your continued
                                    use after changes constitutes acceptance of the updated policy.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
                                <p className="text-muted-foreground">
                                    For privacy-related questions or requests:<br />
                                    Email: nmove.co@gmail.com<br />
                                    Address: Astana, Kazakhstan
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

export default PrivacyPolicy;
