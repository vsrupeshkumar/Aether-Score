"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { WalletComparison } from "./WalletComparison";
import { BenchmarkComparison } from "./BenchmarkComparison";
import { InsightsPanel } from "./InsightsPanel";

interface AnalyticsDashboardProps {
  address: string;
}

export function AnalyticsDashboard({ address }: AnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/analytics/comprehensive/${address}`);
        if (!response.ok) {
          throw new Error("Failed to fetch analytics");
        }
        const data = await response.json();
        setAnalytics(data);
      } catch (error) {
        console.error("Error fetching analytics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [address]);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      <ScoreBreakdown address={address} />
      <WalletComparison address={address} />
      <BenchmarkComparison address={address} />
      <InsightsPanel address={address} />
    </div>
  );
}

