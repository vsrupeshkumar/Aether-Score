'use client';

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Home, 
  LayoutDashboard, 
  MessageSquare, 
  Lock, 
  Coins,
  Wallet,
  LogOut
} from "lucide-react";
import { cn } from "@/app/lib/utils";
import { AETHER-SCORELogo } from "@/components/AETHER-SCORELogo";

interface NavItem {
  icon: React.ElementType;
  label: string;
  path: string;
}

const navItems: NavItem[] = [
  { icon: Home, label: "Home", path: "/" },
  { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
  { icon: MessageSquare, label: "NeuroLend", path: "/lend" },
  { icon: Lock, label: "Stake", path: "/stake" },
  { icon: Coins, label: "DeFi Demo", path: "/lending-demo" },
];

interface SidebarProps {
  isConnected: boolean;
  walletAddress?: string;
  balance?: string;
  onConnect: () => void;
  onDisconnect: () => void;
}

export function Sidebar({ 
  isConnected, 
  walletAddress, 
  balance,
  onConnect, 
  onDisconnect 
}: SidebarProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setIsExpanded(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isExpanded ? 256 : 72 }}
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
        className={cn(
          "fixed left-0 top-0 h-screen z-50",
          "glass border-r border-border/30",
          "flex flex-col",
          "transition-all duration-300"
        )}
      >
        {/* Logo */}
        <div className="p-4 border-b border-border/30">
          <Link href="/" className="flex items-center">
            <AnimatePresence mode="wait">
              {isExpanded ? (
                <motion.div
                  key="expanded"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="w-full"
                >
                  <AETHER-SCORELogo size="md" showText={true} />
                </motion.div>
              ) : (
                <motion.div
                  key="collapsed"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="w-full flex justify-center"
                >
                  <AETHER-SCORELogo size="sm" showText={false} />
                </motion.div>
              )}
            </AnimatePresence>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.path || (item.path !== '/' && pathname?.startsWith(item.path));
            const Icon = item.icon;
            
            return (
              <Link
                key={item.path}
                href={item.path}
                className={cn(
                  "flex items-center gap-3 px-3 py-3 rounded-lg",
                  "transition-all duration-200",
                  "group relative",
                  isActive 
                    ? "bg-gradient-primary text-primary-foreground shadow-[0_0_20px_hsl(var(--primary)/0.3)]" 
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full"
                    style={{ left: -12 }}
                  />
                )}
                <Icon className="w-5 h-5 flex-shrink-0" />
                <AnimatePresence>
                  {isExpanded && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            );
          })}
        </nav>

        {/* Wallet Section */}
        <div className="p-3 border-t border-border/30">
          {isConnected ? (
            <div className="space-y-2">
              <div className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg",
                "glass-subtle border border-border/30"
              )}>
                <div className="relative">
                  <div className="w-8 h-8 rounded-full bg-success/20 flex items-center justify-center">
                    <Wallet className="w-4 h-4 text-success" />
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-success rounded-full border-2 border-card animate-pulse" />
                </div>
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="overflow-hidden flex-1 min-w-0"
                    >
                      <p className="text-xs text-muted-foreground">Connected</p>
                      <p className="text-sm font-mono truncate">{walletAddress}</p>
                      {balance && (
                        <p className="text-xs text-primary font-mono">{balance} QIE</p>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              
              <AnimatePresence>
                {isExpanded && (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onDisconnect}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-destructive hover:bg-destructive/10 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm">Disconnect</span>
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <button
              onClick={onConnect}
              className={cn(
                "w-full flex items-center justify-center gap-2",
                "px-3 py-3 rounded-lg",
                "bg-gradient-primary text-primary-foreground font-medium",
                "hover:shadow-[0_0_30px_hsl(var(--primary)/0.4)]",
                "transition-all duration-300"
              )}
            >
              <Wallet className="w-5 h-5" />
              <AnimatePresence>
                {isExpanded && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="whitespace-nowrap"
                  >
                    Connect Wallet
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          )}
        </div>
      </motion.aside>
    </>
  );
}

