"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface BenchmarkComparisonProps {
  address: string;
  industry?: string;
}

export function BenchmarkComparison({ address, industry }: BenchmarkComparisonProps) {
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        const url = industry
          ? `${getApiUrl()}/api/analytics/benchmark/${address}?industry=${industry}`
          : `${getApiUrl()}/api/analytics/benchmark/${address}`;
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error("Failed to fetch benchmark comparison");
        }
        const data = await response.json();
        setComparison(data);
      } catch (error) {
        console.error("Error fetching benchmark comparison:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [address, industry]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!comparison) {
    return <div>No benchmark data available</div>;
  }

  const chartData = [
    {
      name: "Your Score",
      score: comparison.wallet_score || 0,
    },
    {
      name: "Industry Average",
      score: comparison.benchmark?.average_score || 0,
    },
    {
      name: "Industry Median",
      score: comparison.benchmark?.median_score || 0,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Industry Benchmark Comparison</CardTitle>
        <CardDescription>
          Compare your score with {comparison.industry || "industry"} benchmarks
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-xl font-bold">
                {comparison.comparison?.vs_average > 0 ? "+" : ""}
                {comparison.comparison?.vs_average || 0}
              </div>
              <div className="text-sm text-gray-600">vs Average</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-xl font-bold">
                {comparison.comparison?.percentile?.toFixed(1) || 0}%
              </div>
              <div className="text-sm text-gray-600">Percentile</div>
            </div>
          </div>

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

          {comparison.benchmark_data && (
            <div className="space-y-2">
              <h3 className="font-medium">Industry Statistics</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Sample Size:</span>{" "}
                  <span className="font-medium">{comparison.benchmark_data.sample_size}</span>
                </div>
                <div>
                  <span className="text-gray-500">Min Score:</span>{" "}
                  <span className="font-medium">{comparison.benchmark_data.min_score}</span>
                </div>
                <div>
                  <span className="text-gray-500">Max Score:</span>{" "}
                  <span className="font-medium">{comparison.benchmark_data.max_score}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

