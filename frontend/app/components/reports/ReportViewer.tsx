"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { getApiUrl } from "@/lib/api";
import { LoadingSpinner } from "@/app/components/ui/LoadingSpinner";

interface ReportViewerProps {
  reportId: number;
}

export function ReportViewer({ reportId }: ReportViewerProps) {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/reports/${reportId}`);
        if (!response.ok) {
          throw new Error("Failed to fetch report");
        }
        const data = await response.json();
        setReport(data);
      } catch (error) {
        console.error("Error fetching report:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [reportId]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!report) {
    return <div>Report not found</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Credit Report</CardTitle>
        <CardDescription>
          Generated: {new Date(report.generated_at).toLocaleDateString()}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <strong>Report Type:</strong> {report.report_type}
          </div>
          <div>
            <strong>Format:</strong> {report.format}
          </div>
          {report.file_url && (
            <a
              href={`${getApiUrl()}${report.file_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Download Report
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

