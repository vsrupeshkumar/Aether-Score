'use client';

import { useState, useEffect } from 'react';
import { History, CheckCircle, XCircle } from 'lucide-react';
import { getApiUrl } from '@/lib/api';

interface RewardHistory {
  id: number;
  reward_type: string;
  amount_ncrd: number;
  status: string;
  distribution_tx_hash?: string;
  distributed_at?: string;
  created_at: string;
}

interface ReferralHistoryProps {
  address: string;
}

export function ReferralHistory({ address }: ReferralHistoryProps) {
  const [history, setHistory] = useState<RewardHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/referrals/rewards/history?address=${address}`);
        if (response.ok) {
          const data = await response.json();
          setHistory(data.rewards || []);
        }
      } catch (error) {
        console.error('Error fetching reward history:', error);
      } finally {
        setLoading(false);
      }
    };

    if (address) {
      fetchHistory();
    }
  }, [address]);

  if (loading) {
    return <div className="animate-pulse bg-gray-200 rounded-lg h-64" />;
  }

  return (
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
        <History className="w-5 h-5" />
        Reward History
      </h3>

      {history.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No reward history
        </div>
      ) : (
        <div className="space-y-2">
          {history.map((reward) => (
            <div
              key={reward.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                {reward.status === 'distributed' ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : reward.status === 'failed' ? (
                  <XCircle className="w-4 h-4 text-red-500" />
                ) : (
                  <History className="w-4 h-4 text-yellow-500" />
                )}
                <div>
                  <div className="font-medium capitalize">{reward.reward_type}</div>
                  <div className="text-sm text-gray-500">
                    {new Date(reward.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">{reward.amount_ncrd.toFixed(2)} NCRD</div>
                <div className="text-xs text-gray-500 capitalize">{reward.status}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

