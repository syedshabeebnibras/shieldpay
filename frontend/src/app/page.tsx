"use client";

import Link from "next/link";
import { motion, useInView } from "framer-motion";
import {
  ArrowRight,
  Check,
  ClipboardList,
  Link2,
  Lock,
  Scale,
  Shield,
  ShieldCheck,
  Star,
  TrendingUp,
  Wallet,
  Zap,
} from "lucide-react";
import { useRef } from "react";
import { useAnimatedCounter } from "@/hooks/useAnimatedCounter";

// ── Framer variants ──────────────────────────────────────────────────

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
};

const stagger = {
  visible: { transition: { staggerChildren: 0.15 } },
};

function Section({
  children,
  className = "",
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  return (
    <motion.section
      ref={ref}
      id={id}
      initial="hidden"
      animate={inView ? "visible" : "hidden"}
      variants={stagger}
      className={`px-6 ${className}`}
    >
      {children}
    </motion.section>
  );
}

// ── Page ─────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <div className="min-h-screen bg-white font-[family-name:var(--font-geist-sans)]">
      <Nav />
      <Hero />
      <ProblemStats />
      <HowItWorks />
      <Features />
      <Pricing />
      <Testimonials />
      <CTASection />
      <Footer />
    </div>
  );
}

// ── Nav ──────────────────────────────────────────────────────────────

function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur-lg">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold text-gray-900">
          <Shield className="h-6 w-6 text-blue-600" />
          ShieldPay
        </Link>
        <nav className="hidden items-center gap-6 text-sm font-medium text-gray-600 md:flex">
          <a href="#how-it-works" className="hover:text-gray-900">How It Works</a>
          <a href="#features" className="hover:text-gray-900">Features</a>
          <a href="#pricing" className="hover:text-gray-900">Pricing</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900">
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm shadow-blue-600/20 hover:bg-blue-700"
          >
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

// ── Hero ─────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section className="relative overflow-hidden pb-20 pt-20 md:pt-32">
      {/* Gradient blobs */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2">
        <div className="h-[500px] w-[800px] rounded-full bg-blue-100/60 blur-3xl" />
      </div>
      <div className="pointer-events-none absolute right-0 top-20">
        <div className="h-[300px] w-[300px] rounded-full bg-emerald-100/40 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700">
            <ShieldCheck className="h-4 w-4" />
            Escrow-backed payment protection
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-5xl font-bold leading-tight tracking-tight text-gray-900 md:text-7xl"
        >
          Get Paid for
          <br />
          Every Project.{" "}
          <span className="bg-gradient-to-r from-blue-600 to-emerald-500 bg-clip-text text-transparent">
            Guaranteed.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto mt-6 max-w-2xl text-lg text-gray-600 md:text-xl"
        >
          Escrow-backed payment protection for freelancers.
          No platform lock-in. No 20% fees. Just guaranteed payment.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
        >
          <Link
            href="/register"
            className="group flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-blue-600/25 transition-all hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-600/30"
          >
            Start Protecting Your Payments
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <a
            href="#how-it-works"
            className="rounded-xl border border-gray-200 px-8 py-4 text-base font-semibold text-gray-700 transition-colors hover:bg-gray-50"
          >
            See How It Works
          </a>
        </motion.div>

        {/* Trust indicators */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500"
        >
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-gray-400" />
            256-bit encryption
          </div>
          <div className="h-4 w-px bg-gray-200" />
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-gray-400" />
            Powered by Stripe
          </div>
          <div className="h-4 w-px bg-gray-200" />
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-gray-400" />
            3.5% fee only when paid
          </div>
        </motion.div>

        {/* Animated escrow flow */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-16"
        >
          <EscrowFlowDiagram />
        </motion.div>
      </div>
    </section>
  );
}

function EscrowFlowDiagram() {
  const steps = [
    { label: "Client", sub: "Sends Payment", color: "blue" },
    { label: "ShieldPay", sub: "Holds in Escrow", color: "emerald" },
    { label: "Freelancer", sub: "Receives on Approval", color: "blue" },
  ];

  return (
    <div className="mx-auto flex max-w-xl items-center justify-between">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center">
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ repeat: Infinity, duration: 3, delay: i * 0.5 }}
            className={`flex flex-col items-center rounded-2xl border-2 px-6 py-4 ${
              step.color === "emerald"
                ? "border-emerald-200 bg-emerald-50"
                : "border-blue-200 bg-blue-50"
            }`}
          >
            <span className={`text-sm font-bold ${
              step.color === "emerald" ? "text-emerald-700" : "text-blue-700"
            }`}>
              {step.label}
            </span>
            <span className="mt-0.5 text-xs text-gray-500">{step.sub}</span>
          </motion.div>
          {i < steps.length - 1 && (
            <motion.div
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ repeat: Infinity, duration: 2, delay: i * 0.5 }}
              className="mx-2 flex items-center text-gray-300"
            >
              <div className="h-px w-8 bg-gray-300 md:w-16" />
              <ArrowRight className="h-4 w-4" />
            </motion.div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Problem Stats ────────────────────────────────────────────────────

function StatCounter({
  value,
  suffix,
  prefix,
  label,
}: {
  value: number;
  suffix?: string;
  prefix?: string;
  label: string;
}) {
  const { count, ref } = useAnimatedCounter(value);
  return (
    <div className="text-center">
      <span ref={ref} className="text-4xl font-bold text-gray-900 md:text-5xl">
        {prefix}
        {count.toLocaleString()}
        {suffix}
      </span>
      <p className="mt-2 text-sm text-gray-500">{label}</p>
    </div>
  );
}

function ProblemStats() {
  return (
    <Section className="bg-gray-50 py-20" id="problem">
      <div className="mx-auto max-w-5xl">
        <motion.p
          variants={fadeUp}
          className="text-center text-sm font-semibold uppercase tracking-wider text-red-500"
        >
          The freelancer payment crisis
        </motion.p>
        <motion.h2
          variants={fadeUp}
          className="mt-3 text-center text-3xl font-bold text-gray-900 md:text-4xl"
        >
          You deserve to get paid. Every time.
        </motion.h2>
        <motion.div
          variants={stagger}
          className="mt-12 grid gap-8 md:grid-cols-3"
        >
          <motion.div variants={fadeUp}>
            <StatCounter value={85} suffix="%" label="of freelancers experience late or non-payment" />
          </motion.div>
          <motion.div variants={fadeUp}>
            <StatCounter value={6000} prefix="$" label="lost per year by the average freelancer" />
          </motion.div>
          <motion.div variants={fadeUp}>
            <StatCounter value={100} suffix="+" label="hours/year spent chasing invoices" />
          </motion.div>
        </motion.div>
      </div>
    </Section>
  );
}

// ── How It Works ─────────────────────────────────────────────────────

function HowItWorks() {
  const steps = [
    {
      icon: ClipboardList,
      title: "Create a Project",
      description: "Define milestones and amounts. We generate a professional payment page.",
    },
    {
      icon: Link2,
      title: "Share Payment Link",
      description: "Send one link to your client. They fund milestones via Stripe.",
    },
    {
      icon: ShieldCheck,
      title: "Client Funds Escrow",
      description: "Money is held securely by ShieldPay. The client can't take it back.",
    },
    {
      icon: Wallet,
      title: "Get Paid on Approval",
      description: "Deliver work, client approves, funds release to your bank instantly.",
    },
  ];

  return (
    <Section className="py-20" id="how-it-works">
      <div className="mx-auto max-w-5xl">
        <motion.p
          variants={fadeUp}
          className="text-center text-sm font-semibold uppercase tracking-wider text-blue-600"
        >
          Simple & secure
        </motion.p>
        <motion.h2
          variants={fadeUp}
          className="mt-3 text-center text-3xl font-bold text-gray-900 md:text-4xl"
        >
          How ShieldPay Works
        </motion.h2>

        <motion.div variants={stagger} className="mt-14 grid gap-8 md:grid-cols-4">
          {steps.map((step, i) => (
            <motion.div key={step.title} variants={fadeUp} className="relative text-center">
              {i < steps.length - 1 && (
                <div className="absolute left-full top-8 hidden h-px w-full bg-gray-200 md:block" />
              )}
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                <step.icon className="h-7 w-7" />
              </div>
              <div className="mt-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
                {i + 1}
              </div>
              <h3 className="mt-3 text-base font-semibold text-gray-900">
                {step.title}
              </h3>
              <p className="mt-2 text-sm text-gray-500">{step.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </Section>
  );
}

// ── Features ─────────────────────────────────────────────────────────

function Features() {
  const features = [
    {
      icon: ShieldCheck,
      title: "Escrow Protection",
      description: "Funds held securely until you deliver. Your work is never free.",
    },
    {
      icon: TrendingUp,
      title: "Milestone Payments",
      description: "Break projects into funded stages. Get paid as you progress.",
    },
    {
      icon: Star,
      title: "Client Reputation",
      description: "See client payment history and trust scores before accepting work.",
    },
    {
      icon: ClipboardList,
      title: "Smart Contracts",
      description: "Auto-generated agreements with payment terms. No paperwork.",
    },
    {
      icon: Zap,
      title: "Instant Payouts",
      description: "Approved funds released to your bank within 2 business days.",
    },
    {
      icon: Scale,
      title: "Dispute Resolution",
      description: "Fair, impartial mediation if disagreements arise. Funds stay frozen.",
    },
  ];

  return (
    <Section className="bg-gray-50 py-20" id="features">
      <div className="mx-auto max-w-5xl">
        <motion.p
          variants={fadeUp}
          className="text-center text-sm font-semibold uppercase tracking-wider text-blue-600"
        >
          Everything you need
        </motion.p>
        <motion.h2
          variants={fadeUp}
          className="mt-3 text-center text-3xl font-bold text-gray-900 md:text-4xl"
        >
          Built for Freelancers
        </motion.h2>

        <motion.div
          variants={stagger}
          className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3"
        >
          {features.map((f) => (
            <motion.div
              key={f.title}
              variants={fadeUp}
              whileHover={{ y: -4 }}
              className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-base font-semibold text-gray-900">
                {f.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-500">
                {f.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </Section>
  );
}

// ── Pricing ──────────────────────────────────────────────────────────

function Pricing() {
  const comparisons = [
    { platform: "ShieldPay", fee: "3.5%", example: "$175", highlight: true },
    { platform: "Upwork", fee: "10-20%", example: "$500-1,000", highlight: false },
    { platform: "Fiverr", fee: "20%", example: "$1,000", highlight: false },
  ];

  return (
    <Section className="py-20" id="pricing">
      <div className="mx-auto max-w-3xl">
        <motion.p
          variants={fadeUp}
          className="text-center text-sm font-semibold uppercase tracking-wider text-emerald-600"
        >
          Simple pricing
        </motion.p>
        <motion.h2
          variants={fadeUp}
          className="mt-3 text-center text-3xl font-bold text-gray-900 md:text-4xl"
        >
          3.5% per transaction. That&apos;s it.
        </motion.h2>
        <motion.p
          variants={fadeUp}
          className="mt-3 text-center text-gray-500"
        >
          No monthly fees. No hidden charges. You only pay when you get paid.
        </motion.p>

        <motion.div variants={fadeUp} className="mt-10">
          <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
            <div className="bg-gray-50 px-6 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
              On a $5,000 project
            </div>
            {comparisons.map((c) => (
              <div
                key={c.platform}
                className={`flex items-center justify-between px-6 py-4 ${
                  c.highlight
                    ? "bg-blue-50/50 border-l-4 border-blue-600"
                    : "border-b border-gray-100"
                }`}
              >
                <div className="flex items-center gap-3">
                  {c.highlight && (
                    <Check className="h-5 w-5 text-blue-600" />
                  )}
                  <span
                    className={`font-medium ${
                      c.highlight ? "text-blue-700" : "text-gray-700"
                    }`}
                  >
                    {c.platform}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-sm text-gray-500">{c.fee}</span>
                  <span className="ml-4 font-semibold text-gray-900">
                    {c.example}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-4 text-center text-xs text-gray-400">
            You save $325-825 on every $5,000 project compared to traditional platforms.
          </p>
        </motion.div>
      </div>
    </Section>
  );
}

// ── Testimonials ─────────────────────────────────────────────────────

function Testimonials() {
  const testimonials = [
    {
      quote:
        "ShieldPay changed my freelance business. I no longer stress about whether I'll get paid.",
      name: "Sarah Chen",
      role: "UX Designer",
      rating: 5,
    },
    {
      quote:
        "The milestone system is brilliant. My clients love the transparency, and I love the security.",
      name: "Marcus Johnson",
      role: "Web Developer",
      rating: 5,
    },
    {
      quote:
        "Switched from Upwork. Saving thousands in fees and my clients prefer the direct relationship.",
      name: "Elena Rodriguez",
      role: "Brand Strategist",
      rating: 5,
    },
  ];

  return (
    <Section className="bg-gray-50 py-20">
      <div className="mx-auto max-w-5xl">
        <motion.h2
          variants={fadeUp}
          className="text-center text-3xl font-bold text-gray-900"
        >
          Loved by Freelancers
        </motion.h2>
        <motion.div
          variants={stagger}
          className="mt-12 grid gap-6 md:grid-cols-3"
        >
          {testimonials.map((t) => (
            <motion.div
              key={t.name}
              variants={fadeUp}
              className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex gap-0.5">
                {Array.from({ length: t.rating }).map((_, i) => (
                  <Star
                    key={i}
                    className="h-4 w-4 fill-yellow-400 text-yellow-400"
                  />
                ))}
              </div>
              <p className="mt-3 text-sm leading-relaxed text-gray-600">
                &ldquo;{t.quote}&rdquo;
              </p>
              <div className="mt-4 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-600">
                  {t.name.charAt(0)}
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {t.name}
                  </div>
                  <div className="text-xs text-gray-500">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </Section>
  );
}

// ── CTA Section ──────────────────────────────────────────────────────

function CTASection() {
  return (
    <Section className="py-20">
      <motion.div
        variants={fadeUp}
        className="mx-auto max-w-2xl rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 px-8 py-14 text-center shadow-xl shadow-blue-600/20"
      >
        <h2 className="text-3xl font-bold text-white md:text-4xl">
          Stop losing money.
          <br />
          Start every project protected.
        </h2>
        <p className="mt-4 text-blue-100">
          Join thousands of freelancers who never worry about payment again.
        </p>
        <div className="mt-8">
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-semibold text-blue-600 shadow-lg transition-all hover:shadow-xl"
          >
            Get Started Free
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
        <p className="mt-4 text-sm text-blue-200">
          No credit card required. Set up in 2 minutes.
        </p>
      </motion.div>
    </Section>
  );
}

// ── Footer ───────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <div className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <Shield className="h-5 w-5 text-blue-600" />
              ShieldPay
            </div>
            <p className="mt-3 text-sm text-gray-500">
              Escrow-backed payment protection for freelancers.
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs text-gray-400">
              <Lock className="h-3.5 w-3.5" />
              Powered by Stripe
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-900">Product</h4>
            <ul className="mt-3 space-y-2 text-sm text-gray-500">
              <li><a href="#how-it-works" className="hover:text-gray-900">How It Works</a></li>
              <li><a href="#features" className="hover:text-gray-900">Features</a></li>
              <li><a href="#pricing" className="hover:text-gray-900">Pricing</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-900">Company</h4>
            <ul className="mt-3 space-y-2 text-sm text-gray-500">
              <li><a href="#" className="hover:text-gray-900">About</a></li>
              <li><a href="#" className="hover:text-gray-900">Blog</a></li>
              <li><a href="#" className="hover:text-gray-900">Contact</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-900">Legal</h4>
            <ul className="mt-3 space-y-2 text-sm text-gray-500">
              <li><a href="#" className="hover:text-gray-900">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-gray-900">Terms of Service</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-12 border-t border-gray-100 pt-8 text-center text-sm text-gray-400">
          &copy; {new Date().getFullYear()} ShieldPay. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
