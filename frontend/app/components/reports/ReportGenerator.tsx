"use client";

import { useState } from "react";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select";
import { getApiUrl } from "@/lib/api";
import { useToast } from "@/app/hooks/use-toast";

interface ReportGeneratorProps {
  address: string;
}

export function ReportGenerator({ address }: ReportGeneratorProps) {
  const [reportType, setReportType] = useState<string>("full");
  const [format, setFormat] = useState<string>("pdf");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const generateReport = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${getApiUrl()}/api/reports/generate?report_type=${reportType}&format=${format}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to generate report");
      }

      const data = await response.json();
      
      toast({
        title: "Report Generated",
        description: "Your credit report has been generated successfully.",
      });

      // If PDF, trigger download
      if (format === "pdf" && data.file_url) {
        window.open(`${getApiUrl()}${data.file_url}`, "_blank");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to generate report",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Credit Report</CardTitle>
        <CardDescription>Create a detailed credit report in your preferred format</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Report Type</label>
          <Select value={reportType} onValueChange={setReportType}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="full">Full Report</SelectItem>
              <SelectItem value="summary">Summary</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Format</label>
          <Select value={format} onValueChange={setFormat}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pdf">PDF</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
              <SelectItem value="csv">CSV</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button onClick={generateReport} disabled={loading} className="w-full">
          {loading ? "Generating..." : "Generate Report"}
        </Button>
      </CardContent>
    </Card>
  );
}

