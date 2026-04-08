import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useState, useRef, Suspense } from "react";
import { Link, useLocation } from "react-router-dom";
import { Canvas, useFrame } from "@react-three/fiber";
import {
    Sphere,
    MeshDistortMaterial,
    Float,
    Stars,
    Torus,
    Box,
    OrbitControls,
    MeshWobbleMaterial,
} from "@react-three/drei";
import * as THREE from "three";
import {
    Briefcase,
    AlertTriangle,
    CheckCircle,
    ArrowRight,
    Shield,
    BarChart3,
    TrendingDown,
    Users,
    LineChart,
    FileDown,
    Activity,
    Target,
    Menu,
    X,
} from "lucide-react";

const employerNavLinks = [
    { name: "Problem", href: "#problem" },
    { name: "Dashboard", href: "#dashboard" },
    { name: "Use Cases", href: "#use-cases" },
    { name: "Pricing", href: "#pricing" },
];

function EmployerNavbar() {
    const [open, setOpen] = useState(false);

    const scrollTo = (id: string) => {
        setOpen(false);
        const el = document.querySelector(id);
        if (el) el.scrollIntoView({ behavior: "smooth" });
    };

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-background/70 backdrop-blur-xl border-b border-violet-500/20">
            <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-2">
                    <img src="/logo.jpeg" alt="NMove" className="w-8 h-8 rounded-sm object-contain" />
                    <span className="font-bold text-lg text-foreground">NMove</span>
                    <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30">
                        For Business
                    </span>
                </Link>

                {/* Desktop links */}
                <div className="hidden md:flex items-center gap-8">
                    {employerNavLinks.map((l) => (
                        <button
                            key={l.name}
                            onClick={() => scrollTo(l.href)}
                            className="text-sm text-muted-foreground hover:text-violet-300 transition-colors"
                        >
                            {l.name}
                        </button>
                    ))}
                </div>

                {/* CTAs */}
                <div className="hidden md:flex items-center gap-3">
                    <Link to="/">
                        <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                            ← Main Site
                        </Button>
                    </Link>
                    <button onClick={() => scrollTo("#contact-form")}>
                        <Button
                            size="sm"
                            className="bg-violet-600 hover:bg-violet-500 text-white"
                        >
                            Request Demo
                        </Button>
                    </button>
                </div>

                {/* Mobile toggle */}
                <button className="md:hidden text-foreground p-2" onClick={() => setOpen(!open)}>
                    {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                </button>
            </div>

            {/* Mobile menu */}
            {open && (
                <div className="md:hidden bg-background/95 backdrop-blur-xl border-b border-violet-500/20">
                    <div className="container mx-auto px-6 py-4 space-y-4">
                        {employerNavLinks.map((l) => (
                            <button
                                key={l.name}
                                onClick={() => scrollTo(l.href)}
                                className="block w-full text-left text-sm text-muted-foreground hover:text-violet-300 transition-colors"
                            >
                                {l.name}
                            </button>
                        ))}
                        <div className="pt-2 space-y-2">
                            <button onClick={() => scrollTo("#contact-form")} className="w-full">
                                <Button className="w-full bg-violet-600 hover:bg-violet-500 text-white">
                                    Request Demo
                                </Button>
                            </button>
                            <Link to="/" onClick={() => setOpen(false)}>
                                <Button variant="outline" className="w-full border-border">
                                    ← Main Site
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            )}
        </nav>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// 3-D Hero Scene Components
// ─────────────────────────────────────────────────────────────────────────────

function AnimatedRing() {
    const ref = useRef<THREE.Mesh>(null!);
    useFrame(({ clock }) => {
        ref.current.rotation.x = clock.elapsedTime * 0.25;
        ref.current.rotation.z = clock.elapsedTime * 0.15;
    });
    return (
        <Torus ref={ref} args={[3, 0.15, 32, 120]}>
            <meshStandardMaterial color="#7c3aed" emissive="#4f2dab" emissiveIntensity={0.6} metalness={0.9} roughness={0.1} />
        </Torus>
    );
}

function AnimatedRing2() {
    const ref = useRef<THREE.Mesh>(null!);
    useFrame(({ clock }) => {
        ref.current.rotation.y = clock.elapsedTime * 0.3;
        ref.current.rotation.x = Math.PI / 3 + clock.elapsedTime * 0.1;
    });
    return (
        <Torus ref={ref} args={[2.2, 0.08, 32, 100]}>
            <meshStandardMaterial color="#0ea5e9" emissive="#0369a1" emissiveIntensity={0.5} metalness={0.8} roughness={0.2} />
        </Torus>
    );
}

function CentralSphere() {
    const ref = useRef<THREE.Mesh>(null!);
    useFrame(({ clock }) => {
        ref.current.rotation.y = clock.elapsedTime * 0.18;
    });
    return (
        <Float speed={1.5} floatIntensity={0.6}>
            <Sphere ref={ref} args={[1.3, 128, 128]}>
                <MeshDistortMaterial
                    color="#4f46e5"
                    distort={0.35}
                    speed={2}
                    roughness={0.05}
                    metalness={0.9}
                    emissive="#3730a3"
                    emissiveIntensity={0.3}
                />
            </Sphere>
        </Float>
    );
}

function WobbleSatellite({ position }: { position: [number, number, number] }) {
    return (
        <Float speed={2} floatIntensity={1.2} rotationIntensity={0.8}>
            <Sphere args={[0.3, 32, 32]} position={position}>
                <MeshWobbleMaterial factor={0.4} speed={2} color="#7c3aed" metalness={0.8} roughness={0.1} />
            </Sphere>
        </Float>
    );
}

function FloatingBlocks() {
    const data: { pos: [number, number, number]; color: string; scale: number }[] = [
        { pos: [4, 1.5, -1], color: "#7c3aed", scale: 0.4 },
        { pos: [-4, -1, 0], color: "#0ea5e9", scale: 0.3 },
        { pos: [3.5, -2.5, 0.5], color: "#a855f7", scale: 0.25 },
        { pos: [-3, 2.5, -0.5], color: "#06b6d4", scale: 0.35 },
        { pos: [1.5, 3.5, -0.8], color: "#8b5cf6", scale: 0.2 },
    ];
    return (
        <>
            {data.map((b, i) => (
                <Float key={i} speed={1.2 + i * 0.2} floatIntensity={0.7}>
                    <Box args={[b.scale, b.scale, b.scale]} position={b.pos}>
                        <meshStandardMaterial color={b.color} metalness={0.9} roughness={0.05} emissive={b.color} emissiveIntensity={0.2} />
                    </Box>
                </Float>
            ))}
        </>
    );
}

function ParticleRing() {
    const ref = useRef<THREE.Points>(null!);
    useFrame(({ clock }) => {
        if (ref.current) ref.current.rotation.y = clock.elapsedTime * 0.05;
    });

    const count = 800;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2;
        const radius = 5 + Math.random() * 1.5;
        positions[i * 3] = Math.cos(angle) * radius;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 1.5;
        positions[i * 3 + 2] = Math.sin(angle) * radius;
    }

    return (
        <points ref={ref}>
            <bufferGeometry>
                <bufferAttribute attach="attributes-position" args={[positions, 3]} />
            </bufferGeometry>
            <pointsMaterial size={0.03} color="#a855f7" transparent opacity={0.6} />
        </points>
    );
}

function HeroScene3D() {
    return (
        <Canvas camera={{ position: [0, 0, 9], fov: 50 }} gl={{ antialias: true }}>
            <ambientLight intensity={0.3} />
            <pointLight position={[8, 8, 8]} intensity={2} color="#7c3aed" />
            <pointLight position={[-8, -8, -5]} intensity={1.2} color="#0ea5e9" />
            <pointLight position={[0, 0, 6]} intensity={0.5} color="#ffffff" />
            <Stars radius={100} depth={60} count={4000} factor={4} saturation={0} fade speed={0.8} />
            <Suspense fallback={null}>
                <AnimatedRing />
                <AnimatedRing2 />
                <CentralSphere />
                <WobbleSatellite position={[2.8, 2, 0.5]} />
                <WobbleSatellite position={[-2.5, -1.8, 0.3]} />
                <WobbleSatellite position={[0.5, -2.8, 0]} />
                <FloatingBlocks />
                <ParticleRing />
            </Suspense>
            <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.4} />
        </Canvas>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Data
// ─────────────────────────────────────────────────────────────────────────────

const problems = [
    { text: "Musculoskeletal disorders are one of the leading causes of sick leave.", stat: "#1 cause" },
    { text: "Sedentary work accelerates functional decline in office environments.", stat: "70% sedentary" },
    { text: "Most risk is detected only after pain or injury — when it's already costly.", stat: "Reactive only" },
    { text: "Current screening methods are episodic, manual, and reactive.", stat: "Episodic" },
    { text: "Employers pay after the damage is done.", stat: "Too late", highlight: true },
];

const dashboardFeatures = [
    {
        icon: BarChart3,
        title: "Portfolio Risk Distribution",
        description: "Instant view of your workforce risk spread — low, moderate, high, and critical cohorts in real time.",
        color: "text-violet-400",
        bg: "bg-violet-500/10",
        border: "hover:border-violet-500/40",
    },
    {
        icon: Target,
        title: "High-Risk Group Identification",
        description: "Surface employees with early-stage functional decline before symptoms turn into claims.",
        color: "text-orange-400",
        bg: "bg-orange-500/10",
        border: "hover:border-orange-500/40",
    },
    {
        icon: LineChart,
        title: "Risk Trend Over Time",
        description: "Track whether your workforce is getting healthier or more at-risk, quarter over quarter.",
        color: "text-blue-400",
        bg: "bg-blue-500/10",
        border: "hover:border-blue-500/40",
    },
    {
        icon: Users,
        title: "Engagement & Compliance",
        description: "Monitor program participation and confirm your investment in prevention is actually being used.",
        color: "text-green-400",
        bg: "bg-green-500/10",
        border: "hover:border-green-500/40",
    },
    {
        icon: TrendingDown,
        title: "Risk Reduction Metrics",
        description: "Quantify the impact of wellness programs on functional movement scores over time.",
        color: "text-cyan-400",
        bg: "bg-cyan-500/10",
        border: "hover:border-cyan-500/40",
    },
    {
        icon: FileDown,
        title: "Exportable Reports",
        description: "One-click PDF and CSV exports ready for HR, occupational health, and leadership reviews.",
        color: "text-pink-400",
        bg: "bg-pink-500/10",
        border: "hover:border-pink-500/40",
    },
    {
        icon: Activity,
        title: "Claim Risk Correlation",
        description: "Link functional movement scores directly to historical claim data for predictive underwriting.",
        color: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "hover:border-amber-500/40",
        badge: "Insurers · Coming Soon",
    },
    {
        icon: Shield,
        title: "Underwriting Risk Layer",
        description: "Feed movement risk scores into underwriting models for smarter, fairer pricing.",
        color: "text-indigo-400",
        bg: "bg-indigo-500/10",
        border: "hover:border-indigo-500/40",
        badge: "Insurers · Advanced",
    },
];

const employerUseCases = [
    "Workplace wellness optimization",
    "Reduced sick leave and absenteeism",
    "Proactive health culture",
    "Early intervention for at-risk employees",
];

const insurerUseCases = [
    "Better risk segmentation",
    "Preventive engagement programs",
    "Portfolio-level risk visibility",
    "Reward low-risk policyholders",
];

const pricingOptions = [
    {
        label: "Per Member Per Month (PMPM)",
        description: "Scales cleanly with your covered population — predictable cost, clear ROI.",
    },
    {
        label: "Volume-Based Contracts",
        description: "Better rates for larger programs. The bigger the rollout, the better the unit economics.",
    },
    {
        label: "Pilot Programs",
        description: "Start with a defined cohort, no long-term commitment. Prove value before scaling.",
    },
];

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

const ForEmployers = () => {
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        company: "",
        role: "",
        size: "",
        message: "",
    });
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitted(true);
    };

    return (
        <div className="min-h-screen bg-background">
            {/* ── Dedicated Employer/Insurer Navbar ── */}
            <EmployerNavbar />

            {/* ── HERO — full-screen 3D ── */}
            <section className="relative h-screen flex items-center overflow-hidden">
                {/* 3D canvas — fills the entire hero */}
                <div className="absolute inset-0">
                    <HeroScene3D />
                </div>

                {/* Dark gradient keeps text readable over the 3D scene */}
                <div className="absolute inset-0 bg-gradient-to-r from-background/95 via-background/70 to-transparent pointer-events-none" />

                <div className="relative container mx-auto px-6 pt-16">
                    <div className="max-w-2xl">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/15 text-violet-300 text-sm mb-6 border border-violet-500/25">
                            <Briefcase className="h-4 w-4" />
                            For Employers &amp; Insurers
                        </span>

                        <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6 tracking-tight">
                            Reduce Musculoskeletal{" "}
                            <span className="bg-gradient-to-r from-violet-400 to-blue-400 bg-clip-text text-transparent">
                                Risk Before It Becomes a Claim
                            </span>
                        </h1>

                        <p className="text-xl text-muted-foreground mb-10 leading-relaxed">
                            Continuous functional movement risk monitoring for modern workforces.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4">
                            <a href="#contact-form">
                                <Button
                                    size="lg"
                                    className="bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/40"
                                >
                                    Request Demo
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </a>
                            <a href="#contact-form">
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="border-violet-500/40 text-violet-300 hover:bg-violet-500/10"
                                >
                                    Book Consultation
                                </Button>
                            </a>
                        </div>

                        {/* Scroll hint */}
                        <div className="mt-14 hidden sm:flex items-center gap-3 text-xs text-muted-foreground/60">
                            <div className="w-px h-8 bg-gradient-to-b from-violet-500/60 to-transparent" />
                            Scroll to explore
                        </div>
                    </div>
                </div>
            </section>

            {/* ── THE PROBLEM ── */}
            <section id="problem" className="py-24 bg-muted/20">
                <div className="container mx-auto px-6">
                    <div className="max-w-4xl mx-auto">
                        <div className="text-center mb-14">
                            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 text-orange-400 text-sm mb-4 border border-orange-500/20">
                                <AlertTriangle className="h-4 w-4" />
                                The Challenge
                            </span>
                            <h2 className="text-3xl md:text-4xl font-bold mb-4">
                                The Hidden Cost of Functional Decline
                            </h2>
                            <p className="text-lg text-muted-foreground max-w-lg mx-auto">
                                Your workforce health is declining quietly — until it isn't.
                            </p>
                        </div>

                        <div className="max-w-2xl mx-auto space-y-4">
                            {problems.map((p, i) => (
                                <div
                                    key={i}
                                    className={`flex items-start gap-4 p-5 rounded-xl border transition-all ${p.highlight
                                        ? "bg-orange-500/5 border-orange-500/30"
                                        : "bg-card border-border hover:border-orange-500/20"
                                        }`}
                                >
                                    <div className="w-8 h-8 rounded-full bg-orange-500/10 flex items-center justify-center shrink-0 mt-0.5">
                                        <span className="text-orange-400 font-bold text-xs">{i + 1}</span>
                                    </div>
                                    <div className="flex-1">
                                        <p className={`leading-relaxed text-sm ${p.highlight ? "font-semibold text-foreground" : "text-muted-foreground"}`}>
                                            {p.text}
                                        </p>
                                    </div>
                                    <span className="shrink-0 text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground border border-border whitespace-nowrap">
                                        {p.stat}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* ── DASHBOARD FEATURES ── */}
            <section id="dashboard" className="py-24">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-14">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Employer Dashboard Features</h2>
                        <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                            Everything you need to manage workforce risk at scale — from individual alerts
                            to portfolio-level intelligence.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5 max-w-6xl mx-auto">
                        {dashboardFeatures.map((f) => (
                            <div
                                key={f.title}
                                className={`relative p-6 rounded-2xl bg-card border border-border ${f.border} transition-all duration-200 hover:-translate-y-1`}
                            >
                                {f.badge && (
                                    <span className="absolute top-3 right-3 text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border leading-tight">
                                        {f.badge}
                                    </span>
                                )}
                                <div className={`w-11 h-11 rounded-xl ${f.bg} flex items-center justify-center mb-4`}>
                                    <f.icon className={`h-5 w-5 ${f.color}`} />
                                </div>
                                <h3 className="font-semibold mb-2 leading-snug pr-8">{f.title}</h3>
                                <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── USE CASES ── */}
            <section id="use-cases" className="py-24 bg-muted/20">
                <div className="container mx-auto px-6">
                    <div className="text-center mb-14">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Use Cases</h2>
                        <p className="text-lg text-muted-foreground">
                            NMove adapts to the needs of both employers and insurers.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                        {/* Employers */}
                        <div className="p-8 rounded-2xl bg-card border border-violet-500/20 relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-purple-500" />
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center">
                                    <Briefcase className="h-5 w-5 text-violet-400" />
                                </div>
                                <h3 className="text-xl font-bold">For Employers</h3>
                            </div>
                            <div className="space-y-3">
                                {employerUseCases.map((uc) => (
                                    <div key={uc} className="flex items-center gap-3">
                                        <CheckCircle className="h-4 w-4 text-violet-400 shrink-0" />
                                        <span className="text-muted-foreground text-sm">{uc}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Insurers */}
                        <div className="p-8 rounded-2xl bg-card border border-blue-500/20 relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-cyan-500" />
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                                    <Shield className="h-5 w-5 text-blue-400" />
                                </div>
                                <h3 className="text-xl font-bold">For Insurers</h3>
                            </div>
                            <div className="space-y-3">
                                {insurerUseCases.map((uc) => (
                                    <div key={uc} className="flex items-center gap-3">
                                        <CheckCircle className="h-4 w-4 text-blue-400 shrink-0" />
                                        <span className="text-muted-foreground text-sm">{uc}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── PRICING MODEL ── */}
            <section id="pricing" className="py-24">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto text-center">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm mb-6 border border-emerald-500/20">
                            Flexible Enterprise Pricing
                        </span>
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">
                            No Public Numbers. Just the Right Fit.
                        </h2>
                        <p className="text-lg text-muted-foreground mb-12 max-w-xl mx-auto">
                            We price based on your program size, contract structure, and goals — not a
                            one-size-fits-all tier.
                        </p>

                        <div className="grid md:grid-cols-3 gap-6 mb-12 text-left">
                            {pricingOptions.map((opt, i) => (
                                <div
                                    key={opt.label}
                                    className="p-6 rounded-2xl bg-card border border-border hover:border-emerald-500/30 transition-all"
                                >
                                    <div className="w-2 h-2 rounded-full bg-emerald-400 mb-4" />
                                    <h3 className="font-semibold mb-2 text-sm">{opt.label}</h3>
                                    <p className="text-xs text-muted-foreground leading-relaxed">{opt.description}</p>
                                </div>
                            ))}
                        </div>

                        <a href="#contact-form">
                            <Button
                                size="lg"
                                className="bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/30"
                            >
                                Request Pricing
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </a>
                    </div>
                </div>
            </section>

            {/* ── CONTACT / DEMO FORM ── */}
            <section id="contact-form" className="py-24 bg-muted/20">
                <div className="container mx-auto px-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="text-center mb-10">
                            <h2 className="text-3xl font-bold mb-4">Request a Demo or Consultation</h2>
                            <p className="text-lg text-muted-foreground">
                                Tell us about your workforce and we'll show you exactly what NMove can deliver.
                            </p>
                        </div>

                        {submitted ? (
                            <div className="p-10 rounded-2xl bg-card border border-border text-center">
                                <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-4">
                                    <CheckCircle className="h-8 w-8 text-green-500" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">Got it — we'll be in touch!</h3>
                                <p className="text-muted-foreground">
                                    Our team will reach out within 1–2 business days to schedule your demo or consultation.
                                </p>
                            </div>
                        ) : (
                            <form
                                onSubmit={handleSubmit}
                                className="p-8 rounded-2xl bg-card border border-border space-y-6"
                            >
                                <div className="grid md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <Label htmlFor="emp-name">Full Name *</Label>
                                        <Input
                                            id="emp-name"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            required
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="emp-email">Work Email *</Label>
                                        <Input
                                            id="emp-email"
                                            type="email"
                                            value={formData.email}
                                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                            required
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="emp-company">Company / Organization *</Label>
                                        <Input
                                            id="emp-company"
                                            value={formData.company}
                                            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                                            required
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="emp-role">Your Role</Label>
                                        <Input
                                            id="emp-role"
                                            placeholder="e.g., HR Director, Chief Risk Officer"
                                            value={formData.role}
                                            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-2 md:col-span-2">
                                        <Label htmlFor="emp-size">Workforce / Member Size</Label>
                                        <Input
                                            id="emp-size"
                                            placeholder="e.g., 2,000 employees"
                                            value={formData.size}
                                            onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                                            className="bg-background"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="emp-message">What are you hoping to solve?</Label>
                                    <Textarea
                                        id="emp-message"
                                        value={formData.message}
                                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                        placeholder="Tell us about your musculoskeletal cost challenges, wellness goals, or risk segmentation needs..."
                                        rows={4}
                                        className="bg-background"
                                    />
                                </div>

                                <Button
                                    type="submit"
                                    size="lg"
                                    className="w-full bg-violet-600 hover:bg-violet-500 text-white"
                                >
                                    Send Request
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </form>
                        )}
                    </div>
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default ForEmployers;
