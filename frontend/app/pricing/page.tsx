"""Pricing page for Driftwatch."""
import Link from "next/link";
import { Check, X } from "lucide-react";

const plans = [
  {
    name: "Starter",
    price: "$49",
    period: "/month",
    description: "For indie devs and small projects getting started with API security.",
    features: [
      { text: "3 monitored endpoints", included: true },
      { text: "100K API requests/mo", included: true },
      { text: "Port scanning", included: true },
      { text: "Credential leak detection", included: true },
      { text: "SOC2 report (monthly)", included: true },
      { text: "Email alerts (high/critical)", included: true },
      { text: "Slack integration", included: false },
      { text: "GDPR / ISO27001 reports", included: false },
      { text: "AI alert triage (Claude)", included: false },
      { text: "Priority support", included: false },
    ],
    cta: "Start with Starter",
    href: "/signup?plan=starter",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$149",
    period: "/month",
    description: "For growing startups who need robust security without the enterprise price.",
    features: [
      { text: "20 monitored endpoints", included: true },
      { text: "5M API requests/mo", included: true },
      { text: "Port scanning", included: true },
      { text: "Credential leak detection", included: true },
      { text: "Unlimited SOC2 reports", included: true },
      { text: "Email + Slack alerts", included: true },
      { text: "Slack integration", included: true },
      { text: "GDPR / ISO27001 reports", included: true },
      { text: "AI alert triage (Claude)", included: true },
      { text: "Priority support", included: false },
    ],
    cta: "Start with Pro",
    href: "/signup?plan=pro",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "$299",
    period: "/month",
    description: "For teams that need unlimited scale and dedicated support.",
    features: [
      { text: "Unlimited endpoints", included: true },
      { text: "Unlimited API requests", included: true },
      { text: "Port scanning", included: true },
      { text: "Credential leak detection", included: true },
      { text: "Unlimited compliance reports", included: true },
      { text: "All alert channels", included: true },
      { text: "Slack + custom webhooks", included: true },
      { text: "GDPR / ISO27001 / custom reports", included: true },
      { text: "AI alert triage (Claude)", included: true },
      { text: "Priority support + SLA", included: true },
    ],
    cta: "Start with Enterprise",
    href: "/signup?plan=enterprise",
    highlight: false,
  },
];

const faqs = [
  {
    q: "What counts as a 'monitored endpoint'?",
    a: "An endpoint is any distinct API URL you connect to Driftwatch (e.g. https://api.yoursite.com/v1). Each unique base URL counts as one endpoint.",
  },
  {
    q: "What happens if I exceed my API request limit?",
    a: "Well notify you by email. We don39t cut off your service immediately — you have a 48h grace period to upgrade or降级.",
  },
  {
    q: "Can I switch plans at any time?",
    a: "Yes. Upgrades take effect immediately (charged proration). Downgrades apply at the start of your next billing cycle.",
  },
  {
    q: "Is there a free trial?",
    a: "Yes — every new account starts on a 14-day Starter trial. No credit card required.",
  },
  {
    q: "How does compliance reporting work?",
    a: "Our AI (Claude) analyzes your events, alerts, and scan results to generate audit-ready reports. SOC2 reports are available on all plans; GDPR and ISO27001 on Pro and Enterprise.",
  },
  {
    q: "What39s included in credential leak detection?",
    a: "We hook into your GitHub webhooks and scan every commit for patterns like API keys, passwords, tokens, AWS keys, and private keys. When a leak is found, you get an immediate alert.",
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <svg className="h-6 w-6 text-red-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
            </svg>
            <span className="text-lg font-semibold">Driftwatch</span>
          </Link>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/#features" className="text-slate-400 hover:text-white transition-colors">Features</Link>
            <Link href="/pricing" className="text-white font-medium">Pricing</Link>
            <Link href="/docs" className="text-slate-400 hover:text-white transition-colors">Docs</Link>
            <Link href="/login" className="text-slate-400 hover:text-white transition-colors">Sign in</Link>
            <Link href="/signup" className="px-4 py-1.5 bg-red-600 hover:bg-red-700 rounded-md text-sm font-medium transition-colors">
              Get started
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 text-center px-6">
        <h1 className="text-4xl font-bold mb-4">Security monitoring that doesn't slow you down</h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          One-line integration. Real-time threat detection. Audit-ready compliance reports.
          <br />From indie projects to Series A startups.
        </p>
      </section>

      {/* Pricing Cards */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-xl border p-6 flex flex-col ${
                plan.highlight
                  ? "border-blue-500 bg-blue-950/30 ring-1 ring-blue-500/50"
                  : "border-slate-800 bg-slate-900"
              }`}
            >
              {plan.highlight && (
                <span className="inline-block text-blue-400 text-xs font-semibold mb-2 uppercase tracking-wider">
                  Most popular
                </span>
              )}
              <h2 className="text-xl font-semibold mb-1">{plan.name}</h2>
              <div className="flex items-baseline gap-1 mb-2">
                <span className="text-3xl font-bold">{plan.price}</span>
                <span className="text-slate-500 text-sm">{plan.period}</span>
              </div>
              <p className="text-slate-400 text-sm mb-6">{plan.description}</p>

              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    {f.included ? (
                      <Check className="h-4 w-4 text-green-400 mt-0.5 shrink-0" />
                    ) : (
                      <X className="h-4 w-4 text-slate-600 mt-0.5 shrink-0" />
                    )}
                    <span className={f.included ? "text-slate-300" : "text-slate-600"}>{f.text}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className={`block text-center py-2.5 rounded-md font-medium text-sm transition-colors ${
                  plan.highlight
                    ? "bg-blue-600 hover:bg-blue-700 text-white"
                    : "bg-slate-800 hover:bg-slate-700 text-white border border-slate-700"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-3xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-bold text-center mb-10">Frequently asked questions</h2>
        <div className="space-y-6">
          {faqs.map((faq, i) => (
            <div key={i} className="border border-slate-800 rounded-lg p-5">
              <h3 className="font-medium mb-2">{faq.q}</h3>
              <p className="text-slate-400 text-sm">{faq.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Footer */}
      <section className="border-t border-slate-800 py-16 text-center px-6">
        <h2 className="text-2xl font-bold mb-3">Start protecting your APIs today</h2>
        <p className="text-slate-400 mb-6">14-day free trial. No credit card required. Cancel anytime.</p>
        <Link href="/signup" className="inline-block px-6 py-3 bg-red-600 hover:bg-red-700 rounded-md font-medium transition-colors">
          Create free account
        </Link>
      </section>
    </div>
  );
}