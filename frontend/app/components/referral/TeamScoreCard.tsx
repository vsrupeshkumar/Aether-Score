'use client';

import { Users, Trophy } from 'lucide-react';

interface TeamScoreCardProps {
  teamName: string;
  aggregateScore: number;
  memberCount: number;
  rank?: number;
}

export function TeamScoreCard({ teamName, aggregateScore, memberCount, rank }: TeamScoreCardProps) {
  return (
    <div className="bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-6 text-white">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="w-6 h-6" />
          <h3 className="text-xl font-bold">{teamName}</h3>
        </div>
        {rank && (
          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-300" />
            <span className="text-lg font-semibold">#{rank}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-6">
        <div>
          <div className="text-sm opacity-90">Team Score</div>
          <div className="text-3xl font-bold">{aggregateScore}</div>
        </div>
        <div>
          <div className="text-sm opacity-90">Members</div>
          <div className="text-2xl font-semibold">{memberCount}</div>
        </div>
      </div>
    </div>
  );
}

