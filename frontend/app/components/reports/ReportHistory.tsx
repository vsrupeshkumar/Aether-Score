"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Button } from "@/app/components/ui/button";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";

interface ReportHistoryProps {
  address: string;
}

export function ReportHistory({ address }: ReportHistoryProps) {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/reports`);
        if (!response.ok) {
          throw new Error("Failed to fetch reports");
        }
        const data = await response.json();
        setReports(data.reports || []);
      } catch (error) {
        console.error("Error fetching reports:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Report History</CardTitle>
        <CardDescription>Your generated credit reports</CardDescription>
      </CardHeader>
      <CardContent>
        {reports.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No reports generated yet
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.report_id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div>
                  <div className="font-medium">{report.report_type} Report</div>
                  <div className="text-sm text-gray-500">
                    {new Date(report.generated_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex gap-2">
                  <span className="text-sm text-gray-500">{report.format.toUpperCase()}</span>
                  {report.file_url && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(`${getApiUrl()}${report.file_url}`, "_blank")}
                    >
                      Download
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

