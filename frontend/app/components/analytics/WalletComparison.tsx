"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface WalletComparisonProps {
  address: string;
}

export function WalletComparison({ address }: WalletComparisonProps) {
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/analytics/comparison/${address}`);
        if (!response.ok) {
          throw new Error("Failed to fetch comparison");
        }
        const data = await response.json();
        setComparison(data);
      } catch (error) {
        console.error("Error fetching comparison:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [address]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!comparison) {
    return <div>No comparison data available</div>;
  }

  const chartData = [
    {
      name: "Your Score",
      score: comparison.percentile_rank?.score || 0,
    },
    {
      name: "Average",
      score: comparison.comparison_metrics?.metrics?.score?.average || 0,
    },
    {
      name: "Median",
      score: comparison.comparison_metrics?.metrics?.score?.median || 0,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Wallet Comparison</CardTitle>
        <CardDescription>Compare your score with similar wallets</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {comparison.percentile_rank && (
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold">{comparison.percentile_rank.percentile.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Percentile Rank</div>
              <div className="text-sm text-gray-500 mt-1">
                Rank #{comparison.percentile_rank.rank} out of {comparison.percentile_rank.total_users}
              </div>
            </div>
          )}

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="score" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>

          {comparison.similar_wallets && comparison.similar_wallets.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium">Similar Wallets</h3>
              <div className="space-y-2">
                {comparison.similar_wallets.slice(0, 5).map((wallet: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 border rounded">
                    <div className="text-sm font-mono">{wallet.address.slice(0, 10)}...</div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm">Score: {wallet.score}</span>
                      <span className="text-sm text-gray-500">
                        Similarity: {wallet.similarity_score.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

