"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";
import { AlertCircle, CheckCircle, Info, TrendingUp } from "lucide-react";

interface InsightsPanelProps {
  address: string;
}

export function InsightsPanel({ address }: InsightsPanelProps) {
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/analytics/insights/${address}`);
        if (!response.ok) {
          throw new Error("Failed to fetch insights");
        }
        const data = await response.json();
        setInsights(data);
      } catch (error) {
        console.error("Error fetching insights:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, [address]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!insights) {
    return <div>No insights available</div>;
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "high":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case "medium":
        return <Info className="h-5 w-5 text-yellow-500" />;
      case "low":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Insights & Recommendations</CardTitle>
          <CardDescription>Actionable insights to improve your credit score</CardDescription>
        </CardHeader>
        <CardContent>
          {insights.insights && insights.insights.length > 0 ? (
            <div className="space-y-4">
              {insights.insights.map((insight: any, index: number) => (
                <div
                  key={index}
                  className="flex gap-4 p-4 border rounded-lg"
                >
                  <div className="flex-shrink-0">{getSeverityIcon(insight.severity)}</div>
                  <div className="flex-1">
                    <div className="font-medium mb-2">{insight.message}</div>
                    {insight.suggested_actions && insight.suggested_actions.length > 0 && (
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {insight.suggested_actions.map((action: string, i: number) => (
                          <li key={i}>{action}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No insights available at this time
            </div>
          )}
        </CardContent>
      </Card>

      {insights.recommendations && insights.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
            <CardDescription>Prioritized recommendations to improve your score</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {insights.recommendations.map((rec: any, index: number) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium capitalize">{rec.category.replace(/_/g, " ")}</span>
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        rec.priority === "high"
                          ? "bg-red-100 text-red-800"
                          : rec.priority === "medium"
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-green-100 text-green-800"
                      }`}
                    >
                      {rec.priority}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">
                    Current: {rec.current_score}/{rec.max_score}
                  </div>
                  {rec.recommendations && rec.recommendations.length > 0 && (
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {rec.recommendations.map((r: string, i: number) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

