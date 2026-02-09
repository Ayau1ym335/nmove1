import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Menu, X, ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const navLinks = [
  { name: "Product", href: "/product" },
  {
    name: "Solutions",
    children: [
      { name: "For Patients", href: "/for-patients" },
      { name: "For Clinicians", href: "/for-clinicians" },
    ],
  },
  { name: "Pricing", href: "/pricing" },
  { name: "About", href: "/about" },
  { name: "Blog", href: "/blog" },
];

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (href: string) => location.pathname === href;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border/50">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <img src="/icon.png" alt="NMove" className="w-8 h-8 rounded-sm object-contain" />
          <span className="font-semibold text-lg text-foreground">NMove</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) =>
            link.children ? (
              <DropdownMenu key={link.name}>
                <DropdownMenuTrigger className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
                  {link.name}
                  <ChevronDown className="h-4 w-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent className="bg-card border-border">
                  {link.children.map((child) => (
                    <DropdownMenuItem key={child.href} asChild>
                      <Link
                        to={child.href}
                        className={`w-full cursor-pointer ${isActive(child.href) ? "text-primary" : ""
                          }`}
                      >
                        {child.name}
                      </Link>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Link
                key={link.href}
                to={link.href!}
                className={`text-sm transition-colors ${isActive(link.href!)
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
                  }`}
              >
                {link.name}
              </Link>
            )
          )}
        </div>

        {/* CTA Buttons */}
        <div className="hidden md:flex items-center gap-3">
          <Link to="/contact">
            <Button
              variant="outline"
              size="sm"
              className="border-primary/50 text-primary hover:bg-primary/10"
            >
              Contact
            </Button>
          </Link>
          <Link to="/contact">
            <Button
              size="sm"
              className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary"
            >
              Join Waitlist
            </Button>
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2 text-foreground"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-background/95 backdrop-blur-md border-b border-border">
          <div className="container mx-auto px-6 py-4 space-y-4">
            {navLinks.map((link) =>
              link.children ? (
                <div key={link.name} className="space-y-2">
                  <span className="text-sm font-medium text-foreground">{link.name}</span>
                  <div className="pl-4 space-y-2">
                    {link.children.map((child) => (
                      <Link
                        key={child.href}
                        to={child.href}
                        className={`block text-sm ${isActive(child.href)
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                          }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        {child.name}
                      </Link>
                    ))}
                  </div>
                </div>
              ) : (
                <Link
                  key={link.href}
                  to={link.href!}
                  className={`block text-sm ${isActive(link.href!)
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                    }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.name}
                </Link>
              )
            )}
            <div className="pt-4 flex flex-col gap-2">
              <Link to="/contact" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="outline" className="w-full border-primary/50 text-primary">
                  Contact
                </Button>
              </Link>
              <Link to="/contact" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full bg-primary text-primary-foreground">
                  Join Waitlist
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
