"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Button } from "@/app/components/ui/button";
import { getApiUrl } from "@/lib/api";
import { useToast } from "@/app/hooks/use-toast";
import { TrendingUp, TrendingDown } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface ScoreSimulatorProps {
  address: string;
}

export function ScoreSimulator({ address }: ScoreSimulatorProps) {
  const [stakingAmount, setStakingAmount] = useState<string>("");
  const [transactionCount, setTransactionCount] = useState<string>("");
  const [portfolioValue, setPortfolioValue] = useState<string>("");
  const [loanRepayment, setLoanRepayment] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const scenarios: any = {};
      
      if (stakingAmount) {
        scenarios.staking_amount = parseFloat(stakingAmount);
      }
      if (transactionCount) {
        scenarios.transaction_count = parseInt(transactionCount);
      }
      if (portfolioValue) {
        scenarios.portfolio_value = parseFloat(portfolioValue);
      }
      if (loanRepayment) {
        scenarios.loan_repayment = true;
      }

      if (Object.keys(scenarios).length === 0) {
        toast({
          title: "Error",
          description: "Please specify at least one scenario",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch(`${getApiUrl()}/api/score/simulate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          address,
          scenarios,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to simulate score");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to simulate score",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const chartData = result
    ? [
        {
          name: "Current",
          score: result.current_score || 0,
        },
        {
          name: "Simulated",
          score: result.simulated_score || 0,
        },
      ]
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Simulator</CardTitle>
        <CardDescription>See how different actions would affect your credit score</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="staking">Staking Amount (NCRD)</Label>
            <Input
              id="staking"
              type="number"
              value={stakingAmount}
              onChange={(e) => setStakingAmount(e.target.value)}
              placeholder="1000"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="transactions">Additional Transactions</Label>
            <Input
              id="transactions"
              type="number"
              value={transactionCount}
              onChange={(e) => setTransactionCount(e.target.value)}
              placeholder="50"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="portfolio">Portfolio Value ($)</Label>
            <Input
              id="portfolio"
              type="number"
              value={portfolioValue}
              onChange={(e) => setPortfolioValue(e.target.value)}
              placeholder="5000"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="repayment">Repay Loans</Label>
            <div className="flex items-center space-x-2">
              <input
                id="repayment"
                type="checkbox"
                checked={loanRepayment}
                onChange={(e) => setLoanRepayment(e.target.checked)}
                className="h-4 w-4"
              />
              <label htmlFor="repayment" className="text-sm">
                Repay all outstanding loans
              </label>
            </div>
          </div>
        </div>

        <Button onClick={handleSimulate} disabled={loading} className="w-full">
          {loading ? "Simulating..." : "Simulate Score"}
        </Button>

        {result && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Current Score</div>
                <div className="text-2xl font-bold">{result.current_score || 0}</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-600">Simulated Score</div>
                <div className="text-2xl font-bold text-blue-600">
                  {result.simulated_score || 0}
                </div>
              </div>
              <div
                className={`text-center p-4 rounded-lg ${
                  (result.score_change || 0) >= 0 ? "bg-green-50" : "bg-red-50"
                }`}
              >
                <div className="text-sm text-gray-600">Change</div>
                <div
                  className={`text-2xl font-bold flex items-center justify-center gap-1 ${
                    (result.score_change || 0) >= 0 ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {(result.score_change || 0) >= 0 ? (
                    <TrendingUp className="h-5 w-5" />
                  ) : (
                    <TrendingDown className="h-5 w-5" />
                  )}
                  {result.score_change > 0 ? "+" : ""}
                  {result.score_change || 0}
                </div>
              </div>
            </div>

            {chartData.length > 0 && (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 1000]} />
                  <Tooltip />
                  <Bar dataKey="score" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            )}

            {result.changes && result.changes.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-semibold">Score Changes:</h3>
                {result.changes.map((change: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded"
                  >
                    <span className="text-sm">{change.description}</span>
                    <span
                      className={`font-medium ${
                        change.change >= 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {change.change >= 0 ? "+" : ""}
                      {change.change.toFixed(1)} points
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

