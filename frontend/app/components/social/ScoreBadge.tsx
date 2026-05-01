'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, TrendingUp, Shield } from 'lucide-react';
import { getApiUrl } from '@/lib/api';

interface ScoreBadgeProps {
  address: string;
  style?: 'minimal' | 'detailed' | 'verified';
  score?: number;
  riskBand?: number;
  onShare?: () => void;
}

export function ScoreBadge({ address, style = 'minimal', score, riskBand, onShare }: ScoreBadgeProps) {
  const [badgeData, setBadgeData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBadge = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/social/badge/${address}?style=${style}`);
        if (response.ok) {
          const data = await response.json();
          setBadgeData(data);
        }
      } catch (error) {
        console.error('Error fetching badge:', error);
      } finally {
        setLoading(false);
      }
    };

    if (address) {
      fetchBadge();
    }
  }, [address, style]);

  if (loading) {
    return <div className="animate-pulse bg-gray-200 rounded-lg w-64 h-32" />;
  }

  const displayScore = score || badgeData?.score || 0;
  const displayRiskBand = riskBand || badgeData?.risk_band || 0;
  const riskDescription = badgeData?.risk_description || 'Unknown';

  const riskColors = {
    1: 'text-green-500',
    2: 'text-yellow-500',
    3: 'text-red-500',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-6 text-white shadow-lg"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold">AETHER-SCORE Score</h3>
        {style === 'verified' && (
          <CheckCircle className="w-5 h-5 text-green-300" />
        )}
      </div>
      
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold">{displayScore}</div>
        <div className="flex-1">
          <div className="text-sm opacity-90">/ 1000</div>
          <div className={`text-sm font-semibold ${riskColors[displayRiskBand as keyof typeof riskColors]}`}>
            {riskDescription}
          </div>
        </div>
      </div>

      {style === 'detailed' && badgeData?.explanation && (
        <div className="mt-4 text-xs opacity-80 border-t border-white/20 pt-4">
          {badgeData.explanation}
        </div>
      )}

      {style === 'verified' && badgeData?.on_chain_proof && (
        <div className="mt-4 flex items-center gap-2 text-xs">
          <Shield className="w-4 h-4" />
          <span>Verified on-chain</span>
        </div>
      )}
    </motion.div>
  );
}


