"use client";

import { useState } from "react";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { getApiUrl } from "@/lib/api";
import { useToast } from "@/app/hooks/use-toast";

interface ReportShareProps {
  reportId?: number;
  address: string;
}

export function ReportShare({ reportId, address }: ReportShareProps) {
  const [protocolAddress, setProtocolAddress] = useState("");
  const [expiresInDays, setExpiresInDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const shareReport = async () => {
    if (!protocolAddress) {
      toast({
        title: "Error",
        description: "Protocol address is required",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${getApiUrl()}/api/reports/share`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          protocol_address: protocolAddress,
          report_id: reportId,
          expires_in_days: expiresInDays,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to share report");
      }

      const data = await response.json();
      
      toast({
        title: "Report Shared",
        description: "Your report has been shared successfully.",
      });

      // Copy share URL to clipboard
      if (data.share_url) {
        navigator.clipboard.writeText(`${getApiUrl()}${data.share_url}`);
        toast({
          title: "Share URL Copied",
          description: "The share URL has been copied to your clipboard.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to share report",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Share Report with Protocol</CardTitle>
        <CardDescription>Share your credit report with DeFi protocols</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Protocol Address</label>
          <Input
            value={protocolAddress}
            onChange={(e) => setProtocolAddress(e.target.value)}
            placeholder="0x..."
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Expires In (days)</label>
          <Input
            type="number"
            value={expiresInDays}
            onChange={(e) => setExpiresInDays(parseInt(e.target.value))}
            min={1}
            max={365}
          />
        </div>

        <Button onClick={shareReport} disabled={loading} className="w-full">
          {loading ? "Sharing..." : "Share Report"}
        </Button>
      </CardContent>
    </Card>
  );
}

