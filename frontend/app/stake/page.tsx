'use client';

import { Layout } from '@/components/layout/Layout';
import QIEStaking from '@/app/components/QIEStaking';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/GlassCard';
import { Wallet } from 'lucide-react';
import { useWallet } from '@/contexts/WalletContext';

export default function StakePage() {
  const { address, provider, isConnected, connect } = useWallet();

  return (
    <Layout>
      <div className="min-h-screen px-8 lg:px-16 py-12">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gradient mb-2">NCRD Staking</h1>
            <p className="text-muted-foreground">Stake NCRD tokens to boost your credit score</p>
          </div>

          {!isConnected ? (
            <div className="max-w-md mx-auto">
              <GlassCard className="text-center p-12">
                <div className="text-6xl mb-6">🔒</div>
                <h2 className="text-2xl font-bold mb-4 gradient-text">Connect Your Wallet</h2>
                <p className="text-muted-foreground mb-8">
                  Connect your wallet to start staking NCRD tokens
                </p>
                <Button onClick={connect} variant="glow" size="lg">
                  <Wallet className="w-5 h-5" />
                  Connect Wallet
                </Button>
              </GlassCard>
            </div>
          ) : (
            <QIEStaking address={address} provider={provider} />
          )}
        </div>
      </div>
    </Layout>
  );
}
