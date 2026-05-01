'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ethers } from 'ethers';

interface SidebarProps {
  address: string | null;
  balance?: string;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export default function Sidebar({ address, balance, onConnect, onDisconnect }: SidebarProps) {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const navItems = [
    { href: '/', label: 'Home', icon: 'ðŸ ' },
    { href: '/dashboard', label: 'Dashboard', icon: 'ðŸ“Š' },
    { href: '/lend', label: 'NeuroLend', icon: 'ðŸ’¬' },
    { href: '/stake', label: 'Stake', icon: 'ðŸ”’' },
    { href: '/lending-demo', label: 'DeFi Demo', icon: 'ðŸ’°' },
  ];

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname?.startsWith(href);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden glass p-3 rounded-lg text-white hover:bg-glass-hover transition-all"
        aria-label="Toggle menu"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {isMobileOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Sidebar */}
      <aside
        className={`
          fixed left-0 top-0 h-full w-64 glass z-40
          transform transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
        `}
      >
        <div className="flex flex-col h-full p-6">
          {/* Logo */}
          <Link href="/" className="mb-8 animate-fade-in">
            <h1 className="text-2xl font-bold gradient-text">AETHER-SCORE</h1>
            <p className="text-xs text-text-secondary mt-1">AI Credit Passport</p>
          </Link>

          {/* Navigation */}
          <nav className="flex-1 space-y-2">
            {navItems.map((item, index) => (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg
                  transition-all duration-200
                  animate-slide-up
                  ${isActive(item.href)
                    ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border-l-4 border-cyan-500 text-white'
                    : 'text-text-secondary hover:text-white hover:bg-glass-hover'
                  }
                `}
                style={{ animationDelay: `${index * 0.1}s` }}
                onClick={() => setIsMobileOpen(false)}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Wallet Section */}
          <div className="mt-auto pt-6 border-t border-white/10">
            {address ? (
              <div className="space-y-3 animate-fade-in">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-text-secondary">Connected</span>
                </div>
                <div className="glass p-3 rounded-lg">
                  <p className="text-xs text-text-secondary mb-1">Wallet</p>
                  <p className="text-sm font-mono text-white truncate">
                    {address.slice(0, 6)}...{address.slice(-4)}
                  </p>
                  {balance && (
                    <p className="text-xs text-text-secondary mt-1">
                      {parseFloat(balance).toFixed(4)} QIE
                    </p>
                  )}
                </div>
                {onDisconnect && (
                  <button
                    onClick={onDisconnect}
                    className="w-full px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-all text-sm font-medium"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            ) : (
              <div className="animate-fade-in">
                {onConnect ? (
                  <button
                    onClick={onConnect}
                    className="w-full btn-gradient px-4 py-3 rounded-lg font-semibold"
                  >
                    Connect Wallet
                  </button>
                ) : (
                  <p className="text-xs text-text-secondary text-center">
                    Connect wallet to get started
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}
    </>
  );
}


