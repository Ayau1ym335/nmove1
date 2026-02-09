import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const Success = () => {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <section className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-2xl mx-auto text-center">
                        <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-6">
                            <CheckCircle className="h-10 w-10 text-green-500" />
                        </div>

                        <h1 className="text-4xl font-semibold mb-4">
                            Welcome to <span className="text-gradient-primary">NMove Plus!</span>
                        </h1>

                        <p className="text-lg text-muted-foreground mb-8">
                            Your subscription is now active. We'll send you an email with next steps to get your NMove sensor and start tracking.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Link to="/">
                                <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                                    Go to Home
                                </Button>
                            </Link>
                            <Link to="/for-patients">
                                <Button variant="outline">
                                    Learn More
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

export default Success;
