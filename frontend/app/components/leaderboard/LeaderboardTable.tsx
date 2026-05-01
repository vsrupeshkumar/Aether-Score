'use client';

import { Trophy, Medal, Award } from 'lucide-react';

interface LeaderboardEntry {
  rank: number;
  wallet_address: string;
  score: number;
  risk_band: number;
}

interface LeaderboardTableProps {
  entries: LeaderboardEntry[];
  currentAddress?: string;
}

export function LeaderboardTable({ entries, currentAddress }: LeaderboardTableProps) {
  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-5 h-5 text-gray-400" />;
    if (rank === 3) return <Award className="w-5 h-5 text-orange-500" />;
    return <span className="text-gray-500 font-semibold">#{rank}</span>;
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const getRiskBandColor = (riskBand: number) => {
    const colors = {
      1: 'text-green-600',
      2: 'text-yellow-600',
      3: 'text-red-600',
    };
    return colors[riskBand as keyof typeof colors] || 'text-gray-600';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3 px-4">Rank</th>
            <th className="text-left py-3 px-4">Address</th>
            <th className="text-right py-3 px-4">Score</th>
            <th className="text-center py-3 px-4">Risk Band</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr
              key={entry.rank}
              className={`border-b hover:bg-gray-50 ${
                entry.wallet_address.toLowerCase() === currentAddress?.toLowerCase()
                  ? 'bg-blue-50'
                  : ''
              }`}
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  {getRankIcon(entry.rank)}
                </div>
              </td>
              <td className="py-3 px-4 font-mono text-sm">
                {formatAddress(entry.wallet_address)}
              </td>
              <td className="py-3 px-4 text-right font-semibold">
                {entry.score}
              </td>
              <td className={`py-3 px-4 text-center ${getRiskBandColor(entry.risk_band)}`}>
                {entry.risk_band === 1 ? 'Low' : entry.risk_band === 2 ? 'Medium' : 'High'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

