'use client';

import { Trophy, TrendingUp } from 'lucide-react';

interface UserRankCardProps {
  rank: number;
  score: number;
  riskBand: number;
  category: string;
}

export function UserRankCard({ rank, score, riskBand, category }: UserRankCardProps) {
  const getRankLabel = () => {
    if (rank === 1) return '🥇 1st Place';
    if (rank === 2) return '🥈 2nd Place';
    if (rank === 3) return '🥉 3rd Place';
    return `#${rank}`;
  };

  const getCategoryLabel = () => {
    const labels: Record<string, string> = {
      all_time: 'All-Time',
      monthly: 'This Month',
      weekly: 'This Week',
    };
    return labels[category] || category;
  };

  return (
    <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-6 text-white">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-sm opacity-90">{getCategoryLabel()} Leaderboard</div>
          <div className="text-2xl font-bold">{getRankLabel()}</div>
        </div>
        <Trophy className="w-12 h-12 text-yellow-300" />
      </div>

      <div className="flex items-center gap-4">
        <div>
          <div className="text-sm opacity-90">Your Score</div>
          <div className="text-3xl font-bold">{score}</div>
        </div>
        <div className="flex-1">
          <div className="text-sm opacity-90">Risk Band</div>
          <div className="text-lg font-semibold">
            {riskBand === 1 ? 'Low Risk' : riskBand === 2 ? 'Medium Risk' : 'High Risk'}
          </div>
        </div>
      </div>
    </div>
  );
}

