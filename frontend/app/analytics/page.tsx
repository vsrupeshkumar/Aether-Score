"use client";

import { useWallet } from "@/app/contexts/WalletContext";
import { AnalyticsDashboard } from "@/app/components/analytics/AnalyticsDashboard";
import { Card, CardContent } from "@/app/components/ui/card";

export default function AnalyticsPage() {
  const { address, isConnected } = useWallet();

  if (!isConnected || !address) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="py-8">
            <div className="text-center text-gray-500">
              Please connect your wallet to view analytics
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Advanced Analytics</h1>
        <p className="text-gray-600 mt-2">
          Detailed insights into your credit score and comparison with peers
        </p>
      </div>

      <AnalyticsDashboard address={address} />
    </div>
  );
}

