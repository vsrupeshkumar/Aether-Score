"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

interface ScoreBreakdownProps {
  address: string;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

export function ScoreBreakdown({ address }: ScoreBreakdownProps) {
  const [breakdown, setBreakdown] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBreakdown = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/analytics/breakdown/${address}`);
        if (!response.ok) {
          throw new Error("Failed to fetch breakdown");
        }
        const data = await response.json();
        setBreakdown(data);
      } catch (error) {
        console.error("Error fetching breakdown:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchBreakdown();
  }, [address]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!breakdown || !breakdown.category_scores) {
    return <div>No breakdown data available</div>;
  }

  const chartData = Object.entries(breakdown.category_scores).map(([key, value]: [string, any]) => ({
    name: key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    value: value.score || 0,
    percentage: value.percentage || 0,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Breakdown</CardTitle>
        <CardDescription>Breakdown of your credit score by category</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="text-center">
            <div className="text-4xl font-bold">{breakdown.overall_score}</div>
            <div className="text-sm text-gray-500">Overall Score</div>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>

          <div className="space-y-2">
            {Object.entries(breakdown.category_scores).map(([key, value]: [string, any]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm">
                  {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${value.percentage || 0}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium w-16 text-right">
                    {value.score || 0}/{value.max_score || 0}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

