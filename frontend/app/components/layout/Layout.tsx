'use client';

import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { motion } from "framer-motion";
import { useWallet } from "@/contexts/WalletContext";
import { NetworkIndicator } from "@/app/components/ui/NetworkIndicator";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { isConnected, address, balance, connect, disconnect } = useWallet();

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated background mesh */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <motion.div
          animate={{
            x: [0, 30, -20, 0],
            y: [0, -30, 20, 0],
            scale: [1, 1.1, 0.9, 1],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute top-0 left-0 w-[800px] h-[800px] opacity-30"
          style={{
            background: "radial-gradient(ellipse at center, rgba(0, 212, 255, 0.06) 0%, transparent 70%)",
          }}
        />
        <motion.div
          animate={{
            x: [0, -40, 30, 0],
            y: [0, 40, -30, 0],
            scale: [1, 0.9, 1.1, 1],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute bottom-0 right-0 w-[800px] h-[800px] opacity-30"
          style={{
            background: "radial-gradient(ellipse at center, rgba(124, 58, 237, 0.06) 0%, transparent 70%)",
          }}
        />
        
        {/* Enhanced Grid overlay with visible colored lines */}
        <div className="absolute inset-0 grid-pattern opacity-60" />
        <div className="absolute inset-0 grid-pattern-dense opacity-30" />
        
        {/* Subtle diagonal grid accent */}
        <div 
          className="absolute inset-0 opacity-15"
          style={{
            backgroundImage: `repeating-linear-gradient(
              45deg,
              transparent,
              transparent 2px,
              hsl(var(--primary) / 0.08) 2px,
              hsl(var(--primary) / 0.08) 4px
            )`,
            backgroundSize: '40px 40px'
          }}
        />
        
        {/* Noise texture */}
        <div className="absolute inset-0 noise" />
      </div>

      <Sidebar
        isConnected={isConnected}
        walletAddress={address || undefined}
        balance={balance}
        onConnect={connect}
        onDisconnect={disconnect}
      />

      {/* Main content */}
      <main className="ml-[72px] min-h-screen relative z-10">
        {/* Network Indicator - Fixed at top */}
        <div className="fixed top-4 right-4 z-50">
          <NetworkIndicator />
        </div>
        {children}
      </main>
    </div>
  );
}

