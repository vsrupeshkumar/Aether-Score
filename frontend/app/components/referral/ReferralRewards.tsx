'use client';

import { useState, useEffect } from 'react';
import { Coins, Clock, CheckCircle } from 'lucide-react';
import { getApiUrl } from '@/lib/api';

interface ReferralReward {
  id: number;
  reward_type: string;
  amount_ncrd: number;
  status: string;
  created_at: string;
}

interface ReferralRewardsProps {
  address: string;
}

export function ReferralRewards({ address }: ReferralRewardsProps) {
  const [pendingRewards, setPendingRewards] = useState<ReferralReward[]>([]);
  const [totalPending, setTotalPending] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRewards = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/referrals/rewards/pending?address=${address}`);
        if (response.ok) {
          const data = await response.json();
          setPendingRewards(data.pending_rewards || []);
          setTotalPending(
            (data.pending_rewards || []).reduce((sum: number, r: ReferralReward) => sum + r.amount_ncrd, 0)
          );
        }
      } catch (error) {
        console.error('Error fetching pending rewards:', error);
      } finally {
        setLoading(false);
      }
    };

    if (address) {
      fetchRewards();
    }
  }, [address]);

  if (loading) {
    return <div className="animate-pulse bg-gray-200 rounded-lg h-32" />;
  }

  return (
    <div className="bg-white rounded-lg border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Coins className="w-5 h-5" />
          Pending Rewards
        </h3>
        <div className="text-2xl font-bold text-blue-600">
          {totalPending.toFixed(2)} NCRD
        </div>
      </div>

      {pendingRewards.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No pending rewards
        </div>
      ) : (
        <div className="space-y-2">
          {pendingRewards.map((reward) => (
            <div
              key={reward.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <Clock className="w-4 h-4 text-yellow-500" />
                <div>
                  <div className="font-medium capitalize">{reward.reward_type}</div>
                  <div className="text-sm text-gray-500">
                    {new Date(reward.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <div className="font-semibold">{reward.amount_ncrd.toFixed(2)} NCRD</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

