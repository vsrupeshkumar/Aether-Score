"use client";

import { useEffect, useState } from "react";
import { useWallet } from "@/app/contexts/WalletContext";
import { ReportGenerator } from "@/app/components/reports/ReportGenerator";
import { ReportHistory } from "@/app/components/reports/ReportHistory";
import { ReportShare } from "@/app/components/reports/ReportShare";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs";

export default function ReportsPage() {
  const { address, isConnected } = useWallet();
  const [selectedReportId, setSelectedReportId] = useState<number | undefined>();

  if (!isConnected || !address) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="py-8">
            <div className="text-center text-gray-500">
              Please connect your wallet to view reports
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Credit Reports</h1>
        <p className="text-gray-600 mt-2">
          Generate, view, and share your credit reports
        </p>
      </div>

      <Tabs defaultValue="generate" className="space-y-6">
        <TabsList>
          <TabsTrigger value="generate">Generate Report</TabsTrigger>
          <TabsTrigger value="history">Report History</TabsTrigger>
          <TabsTrigger value="share">Share Report</TabsTrigger>
        </TabsList>

        <TabsContent value="generate">
          <ReportGenerator address={address} />
        </TabsContent>

        <TabsContent value="history">
          <ReportHistory address={address} />
        </TabsContent>

        <TabsContent value="share">
          <ReportShare address={address} reportId={selectedReportId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

