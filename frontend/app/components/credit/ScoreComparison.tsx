"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";

interface ScoreComparisonProps {
  address: string;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28"];

export function ScoreComparison({ address }: ScoreComparisonProps) {
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

  if (!comparison || !comparison.comparison_metrics) {
    return <div>No comparison data available</div>;
  }

  const metrics = comparison.comparison_metrics.metrics;
  const userScore = comparison.percentile_rank?.score || 0;
  const averageScore = metrics?.score?.average || 0;
  const medianScore = metrics?.score?.median || 0;

  const chartData = [
    {
      name: "Your Score",
      score: userScore,
    },
    {
      name: "Average",
      score: averageScore,
    },
    {
      name: "Median",
      score: medianScore,
    },
  ];

  const percentile = comparison.percentile_rank?.percentile || 0;
  const rank = comparison.percentile_rank?.rank || 0;
  const totalUsers = comparison.percentile_rank?.total_users || 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Comparison</CardTitle>
        <CardDescription>Compare your score with other users</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{userScore}</div>
              <div className="text-sm text-gray-600">Your Score</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{averageScore.toFixed(0)}</div>
              <div className="text-sm text-gray-600">Average</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{medianScore.toFixed(0)}</div>
              <div className="text-sm text-gray-600">Median</div>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 1000]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="score" fill="#8884d8">
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="space-y-4">
            <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600">{percentile.toFixed(1)}%</div>
                <div className="text-sm text-gray-600 mt-2">Percentile Rank</div>
                <div className="text-xs text-gray-500 mt-1">
                  Rank #{rank} out of {totalUsers} users
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Min Score:</span>{" "}
                <span className="font-medium">{metrics?.score?.min || 0}</span>
              </div>
              <div>
                <span className="text-gray-500">Max Score:</span>{" "}
                <span className="font-medium">{metrics?.score?.max || 0}</span>
              </div>
            </div>

            {userScore > averageScore && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="text-sm text-green-800">
                  🎉 Your score is above average! Keep up the great work.
                </div>
              </div>
            )}

            {userScore < averageScore && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="text-sm text-yellow-800">
                  💡 Your score is below average. Consider staking NCRD tokens or increasing transaction activity to improve.
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

