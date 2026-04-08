import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowRight, Building2 } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";

export function CTASection() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Connect to backend API
    setSubmitted(true);
  };

  return (
    <section className="py-24 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-radial opacity-30" />

      <div className="container mx-auto px-6 relative z-10">
        <div className="grid md:grid-cols-2 gap-12">
          {/* Individuals CTA */}
          <div className="p-8 md:p-10 rounded-2xl bg-card border border-border">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm mb-6">
              For Individuals
            </div>
            <h3 className="text-2xl md:text-3xl font-semibold mb-4">
              Discover your biological age
            </h3>
            <p className="text-muted-foreground mb-6 leading-relaxed">
              Join our early access list and be among the first to learn your
              biological age, aging velocity, and personal risk profile from
              your walking patterns.
            </p>

            {submitted ? (
              <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30 text-green-500">
                ✓ Thank you! We'll be in touch soon.
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex gap-3">
                <Input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="flex-1 bg-background border-border"
                />
                <Button type="submit" className="bg-primary text-primary-foreground hover:bg-primary/90">
                  Join
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>
            )}
          </div>

          {/* Insurers CTA */}
          <div className="p-8 md:p-10 rounded-2xl bg-gradient-to-br from-primary/10 to-secondary/10 border border-primary/20">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary/20 text-secondary text-sm mb-6">
              <Building2 className="h-4 w-4" />
              For Insurers
            </div>
            <h3 className="text-2xl md:text-3xl font-semibold mb-4">
              Launch a pilot program
            </h3>
            <p className="text-muted-foreground mb-6 leading-relaxed">
              See how biological age scoring can enrich your underwriting models.
              Request a demo and explore integration options for your policyholder
              population.
            </p>
            <Link to="/for-insurers">
              <Button variant="outline" className="border-primary/50 text-primary hover:bg-primary/10">
                Request Insurer Demo
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
