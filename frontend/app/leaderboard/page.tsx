'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { GlassCard } from '@/components/ui/GlassCard';
import { LeaderboardTable } from '@/app/components/leaderboard/LeaderboardTable';
import { UserRankCard } from '@/app/components/leaderboard/UserRankCard';
import { LeaderboardFilters } from '@/app/components/leaderboard/LeaderboardFilters';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useWallet } from '@/contexts/WalletContext';
import { getApiUrl } from '@/lib/api';

export default function LeaderboardPage() {
  const { address } = useWallet();
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [userRank, setUserRank] = useState<any>(null);
  const [category, setCategory] = useState('all_time');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      setLoading(true);
      try {
        const [leaderboardRes, rankRes] = await Promise.all([
          fetch(`${getApiUrl()}/api/leaderboard/${category}?limit=100`),
          address ? fetch(`${getApiUrl()}/api/leaderboard/rank/${address}?category=${category}`) : null,
        ]);

        if (leaderboardRes.ok) {
          const data = await leaderboardRes.json();
          setLeaderboard(data.leaderboard || []);
        }

        if (rankRes && rankRes.ok) {
          const rankData = await rankRes.json();
          setUserRank(rankData);
        }
      } catch (error) {
        console.error('Error fetching leaderboard:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, [category, address]);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-8 px-4">
        <h1 className="text-4xl font-bold mb-8">Leaderboard</h1>

        <LeaderboardFilters category={category} onCategoryChange={setCategory} />

        {userRank && (
          <div className="mb-6">
            <UserRankCard
              rank={userRank.rank}
              score={userRank.score}
              riskBand={userRank.risk_band}
              category={category}
            />
          </div>
        )}

        <GlassCard>
          {loading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : (
            <LeaderboardTable entries={leaderboard} currentAddress={address || undefined} />
          )}
        </GlassCard>
      </div>
    </Layout>
  );
}

