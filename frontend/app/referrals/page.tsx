'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { GlassCard } from '@/components/ui/GlassCard';
import { ReferralRewards } from '@/app/components/referral/ReferralRewards';
import { ReferralHistory } from '@/app/components/referral/ReferralHistory';
import { useWallet } from '@/contexts/WalletContext';
import { getApiUrl } from '@/lib/api';
import { Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ReferralsPage() {
  const { address } = useWallet();
  const [referralCode, setReferralCode] = useState<string>('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchReferralCode = async () => {
      if (!address) return;

      try {
        const response = await fetch(`${getApiUrl()}/api/referrals/stats?address=${address}`);
        if (response.ok) {
          const data = await response.json();
          setReferralCode(data.referral_code || '');
        }
      } catch (error) {
        console.error('Error fetching referral code:', error);
      }
    };

    fetchReferralCode();
  }, [address]);

  const handleCopy = () => {
    if (referralCode) {
      navigator.clipboard.writeText(referralCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const referralUrl = referralCode
    ? `${window.location.origin}?ref=${referralCode}`
    : '';

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-8 px-4">
        <h1 className="text-4xl font-bold mb-8">Referral Program</h1>

        <GlassCard className="mb-6">
          <h2 className="text-2xl font-semibold mb-4">Your Referral Code</h2>
          <div className="flex items-center gap-2 mb-4">
            <input
              type="text"
              value={referralCode || 'Loading...'}
              readOnly
              className="flex-1 border rounded-lg px-4 py-2 font-mono"
            />
            <Button onClick={handleCopy} variant="outline">
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
          </div>
          {referralUrl && (
            <div className="text-sm text-gray-600">
              Share this link: <span className="font-mono text-xs break-all">{referralUrl}</span>
            </div>
          )}
        </GlassCard>

        {address && (
          <>
            <div className="mb-6">
              <ReferralRewards address={address} />
            </div>
            <ReferralHistory address={address} />
          </>
        )}
      </div>
    </Layout>
  );
}

