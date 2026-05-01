'use client';

import { motion } from "framer-motion";
import { ArrowRight, Zap, Shield, Brain, Wallet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/GlassCard";
import { CreditScoreOrb } from "@/components/credit/CreditScoreOrb";
import Link from "next/link";

interface HeroSectionProps {
  isConnected: boolean;
  onConnect: () => void;
  score?: number;
  isConnecting?: boolean;
  isLoading?: boolean;
}

const features = [
  {
    icon: Shield,
    title: "Soulbound NFT",
    description: "Non-transferable credit identity that stays with your wallet forever.",
  },
  {
    icon: Brain,
    title: "AI-Powered",
    description: "Advanced algorithms analyze on-chain behavior for accurate scoring.",
  },
  {
    icon: Zap,
    title: "QIE Native",
    description: "Built specifically for the QIE blockchain ecosystem.",
  },
];

const steps = [
  {
    number: "01",
    icon: Wallet,
    title: "Connect Wallet",
    description: "Link your QIE wallet to begin your credit journey.",
  },
  {
    number: "02",
    icon: Brain,
    title: "AI Analysis",
    description: "Our AI analyzes your on-chain history and behavior patterns.",
  },
  {
    number: "03",
    icon: Shield,
    title: "Get Your Score",
    description: "Receive your soulbound credit passport NFT with your score.",
  },
];

export function HeroSection({ isConnected, onConnect, score, isConnecting = false, isLoading = false }: HeroSectionProps) {
  if (isConnected && score !== undefined) {
    return <ConnectedHero score={score} />;
  }

  return (
    <section className="min-h-screen flex flex-col justify-center px-8 lg:px-16 py-20">
      {/* Main hero content */}
      <div className="max-w-6xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left side - Text content */}
          <div className="space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="space-y-4"
            >
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2, duration: 0.6 }}
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass border border-primary/30"
              >
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                <span className="text-sm text-primary font-medium">QIE Blockchain</span>
              </motion.div>

              <h1 className="text-5xl lg:text-7xl font-bold tracking-tight">
                <span className="text-gradient glow-text">AETHER-SCORE</span>
              </h1>
              
              <p className="text-xl lg:text-2xl text-muted-foreground font-light">
                Your On-Chain Credit Passport
              </p>
            </motion.div>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="text-muted-foreground text-lg max-w-md leading-relaxed"
            >
              AI-powered credit scoring that lives on-chain. Build your DeFi reputation 
              with a soulbound NFT that unlocks better rates and opportunities.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.6 }}
              className="flex flex-wrap gap-4"
            >
              <Button onClick={onConnect} variant="glow" size="xl" disabled={isConnecting || isLoading}>
                {isConnecting || isLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {isConnecting ? 'Connecting...' : 'Generating Score...'}
                  </>
                ) : (
                  <>
                    <Wallet className="w-5 h-5" />
                    Connect Wallet
                  </>
                )}
              </Button>
              <Button variant="glass" size="xl" asChild>
                <a href="#how-it-works">
                  Learn More
                  <ArrowRight className="w-5 h-5" />
                </a>
              </Button>
            </motion.div>
          </div>

          {/* Right side - Visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 1 }}
            className="relative flex items-center justify-center"
          >
            {/* Placeholder score orb for demo */}
            <div className="relative">
              <CreditScoreOrb score={847} size="lg" />
              
              {/* Floating elements */}
              <motion.div
                animate={{ y: [-10, 10, -10] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -top-8 -right-8"
              >
                <GlassCard className="px-3 py-2" hover={false}>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-success/20 flex items-center justify-center">
                      <Zap className="w-3 h-3 text-success" />
                    </div>
                    <span className="text-sm font-mono text-success">+12.5%</span>
                  </div>
                </GlassCard>
              </motion.div>

              <motion.div
                animate={{ y: [10, -10, 10] }}
                transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -bottom-4 -left-12"
              >
                <GlassCard className="px-3 py-2" hover={false}>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                      <Shield className="w-3 h-3 text-primary" />
                    </div>
                    <span className="text-sm text-muted-foreground">Verified</span>
                  </div>
                </GlassCard>
              </motion.div>
            </div>
          </motion.div>
        </div>

        {/* How it works */}
        <motion.div
          id="how-it-works"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="mt-40 pt-20"
        >
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gradient mb-4">How It Works</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Three simple steps to your on-chain credit identity
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15, duration: 0.6 }}
              >
                <GlassCard variant="gradient-border" className="h-full text-center p-8">
                  <div className="relative inline-flex mb-6">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-primary flex items-center justify-center">
                      <step.icon className="w-8 h-8 text-primary-foreground" />
                    </div>
                    <span className="absolute -top-2 -right-2 text-xs font-mono text-primary bg-background px-2 py-1 rounded-full border border-primary/30">
                      {step.number}
                    </span>
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="mt-32"
        >
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gradient mb-4">Features</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Built for the future of decentralized finance
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
              >
                <GlassCard className="h-full">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground text-sm">{feature.description}</p>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function ConnectedHero({ score }: { score: number }) {
  const quickActions = [
    { icon: Brain, label: "NeuroLend", path: "/lend", color: "from-primary to-secondary" },
    { icon: Shield, label: "Stake NCRD", path: "/stake", color: "from-success to-primary" },
    { icon: Zap, label: "DeFi Demo", path: "/lending-demo", color: "from-warning to-destructive" },
  ];

  return (
    <section className="min-h-screen flex flex-col justify-center px-8 lg:px-16 py-20">
      <div className="max-w-6xl mx-auto w-full">
        <div className="grid lg:grid-cols-5 gap-16 items-center">
          {/* Score section - takes 3 columns */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="lg:col-span-3 flex flex-col items-center"
          >
            <div className="mb-8">
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-center mb-8"
              >
                <h1 className="text-3xl font-bold mb-2">Your Credit Score</h1>
                <p className="text-muted-foreground">Based on on-chain analysis</p>
              </motion.div>
              
              <CreditScoreOrb score={score} size="lg" />
            </div>

            {/* Score explanation */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="w-full max-w-md"
            >
              <GlassCard className="text-center">
                <p className="text-muted-foreground text-sm leading-relaxed">
                  Your score reflects your on-chain activity, transaction history, and wallet behavior. 
                  Stake NCRD to boost your score further.
                </p>
              </GlassCard>
            </motion.div>
          </motion.div>

          {/* Quick actions - takes 2 columns */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="lg:col-span-2 space-y-4"
          >
            <h2 className="text-xl font-semibold mb-6">Quick Actions</h2>
            
            {quickActions.map((action, index) => (
              <motion.div
                key={action.label}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
              >
                <Link href={action.path}>
                  <GlassCard className="flex items-center gap-4 p-4 cursor-pointer group">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center transition-transform group-hover:scale-110`}>
                      <action.icon className="w-6 h-6 text-primary-foreground" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold">{action.label}</h3>
                      <p className="text-sm text-muted-foreground">
                        {action.label === "NeuroLend" && "Get personalized loan offers"}
                        {action.label === "Stake NCRD" && "Boost your credit score"}
                        {action.label === "DeFi Demo" && "See your borrowing power"}
                      </p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                  </GlassCard>
                </Link>
              </motion.div>
            ))}

            {/* Stats mini-cards */}
            <div className="grid grid-cols-2 gap-4 pt-4">
              <GlassCard className="p-4 text-center" hover={false}>
                <p className="text-2xl font-bold font-mono text-gradient">$2.45</p>
                <p className="text-xs text-muted-foreground">QIE/USD</p>
              </GlassCard>
              <GlassCard className="p-4 text-center" hover={false}>
                <p className="text-2xl font-bold font-mono text-success">Silver</p>
                <p className="text-xs text-muted-foreground">Stake Tier</p>
              </GlassCard>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

