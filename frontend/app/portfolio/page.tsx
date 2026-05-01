'use client';

import { useWallet } from '@/app/contexts/WalletContext';
import { TokenHoldings } from '@/app/components/portfolio/TokenHoldings';
import { TransactionHistory } from '@/app/components/portfolio/TransactionHistory';
import { TransactionChart } from '@/app/components/portfolio/TransactionChart';
import { DeFiActivity } from '@/app/components/portfolio/DeFiActivity';
import { RiskAssessment } from '@/app/components/portfolio/RiskAssessment';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function PortfolioPage() {
  const { address } = useWallet();

  if (!address) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Portfolio Insights</CardTitle>
            <CardDescription>Please connect your wallet to view your portfolio</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Portfolio Insights</h1>
        <p className="text-muted-foreground">
          Analyze your token holdings, transaction history, DeFi activity, and portfolio risk
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="holdings">Holdings</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="defi">DeFi Activity</TabsTrigger>
          <TabsTrigger value="risk">Risk Assessment</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TokenHoldings />
            <RiskAssessment />
          </div>
          <TransactionChart />
        </TabsContent>

        <TabsContent value="holdings">
          <TokenHoldings />
        </TabsContent>

        <TabsContent value="transactions" className="space-y-6">
          <TransactionChart />
          <TransactionHistory />
        </TabsContent>

        <TabsContent value="defi">
          <DeFiActivity />
        </TabsContent>

        <TabsContent value="risk">
          <RiskAssessment />
        </TabsContent>
      </Tabs>
    </div>
  );
}

