'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { GlassCard } from '@/components/ui/GlassCard';
import { TeamScoreCard } from '@/app/components/referral/TeamScoreCard';
import { LeaderboardTable } from '@/app/components/leaderboard/LeaderboardTable';
import { useWallet } from '@/contexts/WalletContext';
import { getApiUrl } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export default function TeamsPage() {
  const { address } = useWallet();
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/teams/leaderboard?limit=100`);
        if (response.ok) {
          const data = await response.json();
          setLeaderboard(data.leaderboard || []);
        }
      } catch (error) {
        console.error('Error fetching team leaderboard:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, []);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-8 px-4">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold">Team Scores</h1>
          {address && (
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create Team
            </Button>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-pulse">Loading...</div>
          </div>
        ) : (
          <div className="grid gap-6">
            {leaderboard.map((team, index) => (
              <TeamScoreCard
                key={team.team_id}
                teamName={team.team_name}
                aggregateScore={team.aggregate_score}
                memberCount={team.member_count}
                rank={index + 1}
              />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}

