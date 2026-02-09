import { Link } from "react-router-dom";

const footerLinks = {
  product: [
    { name: "Product", href: "/product" },
    { name: "For Patients", href: "/for-patients" },
    { name: "For Clinicians", href: "/for-clinicians" },
    { name: "Pricing", href: "/pricing" },
  ],
  company: [
    { name: "About", href: "/about" },
    { name: "Blog", href: "/blog" },
    { name: "Contact", href: "/contact" },
  ],
  legal: [
    { name: "Privacy Policy", href: "/privacy" },
    { name: "Terms of Service", href: "/terms" },
    { name: "Medical Disclaimer", href: "/medical-disclaimer" },
  ],
};

export function Footer() {
  return (
    <footer className="py-16 border-t border-border bg-background">
      <div className="container mx-auto px-6">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-12">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <img src="/icon.png" alt="NMove" className="w-8 h-8 rounded-sm object-contain" />
              <span className="font-semibold text-lg text-foreground">NMove</span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs mb-4">
              More than just steps. Gait trends between visits—made clear. Helping patients track walking patterns and share clinician-ready reports.
            </p>
            <p className="text-sm text-muted-foreground">
              📍 Astana, Kazakhstan
            </p>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-medium text-foreground mb-4">Product</h4>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="font-medium text-foreground mb-4">Company</h4>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="font-medium text-foreground mb-4">Legal</h4>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-border">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">
              {new Date().getFullYear()} NMove.
            </p>
            <p className="text-xs text-muted-foreground">
              For general wellness purposes only.
            </p>
          </div>
        </div>

        {/* Medical Disclaimer */}
        <div className="mt-8 pt-8 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center max-w-3xl mx-auto leading-relaxed">
            <strong>Important:</strong> NMove is not a medical device and does not provide medical advice, diagnosis, or treatment.
            The information provided is for general wellness and informational purposes only.
            Always consult with a qualified healthcare professional for medical decisions.
            Movement data and trends are supportive tools and should not replace clinical judgment.
          </p>
        </div>
      </div>
    </footer>
  );
}
