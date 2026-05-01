'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useWallet } from '@/app/contexts/WalletContext';
import { getApiUrl } from '@/lib/api';
import { Loader2 } from 'lucide-react';

interface PredictionResult {
  predicted_score: number;
  predicted_change: number;
  current_score: number;
  confidence_level: number;
  explanation: string;
  scenario: string;
}

export function ScorePredictor() {
  const { address } = useWallet();
  const [scenario, setScenario] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [tier, setTier] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    if (!address) {
      setError('Please connect your wallet');
      return;
    }

    if (!scenario) {
      setError('Please select a scenario');
      return;
    }

    setIsLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const scenarioData: Record<string, any> = {};
      if (amount) scenarioData.amount = parseFloat(amount);
      if (tier) scenarioData.tier = parseInt(tier);

      const response = await fetch(`${getApiUrl()}/api/score/${address}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario,
          scenario_data: scenarioData,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to predict score: ${response.statusText}`);
      }

      const data: PredictionResult = await response.json();
      setPrediction(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Predictor</CardTitle>
        <CardDescription>
          Predict how your credit score might change based on different scenarios
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="scenario">Scenario</Label>
          <Select value={scenario} onValueChange={setScenario}>
            <SelectTrigger id="scenario">
              <SelectValue placeholder="Select a scenario" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="loan_repayment">Loan Repayment</SelectItem>
              <SelectItem value="staking">Staking Tokens</SelectItem>
              <SelectItem value="transaction_volume">Increased Transaction Volume</SelectItem>
              <SelectItem value="portfolio_diversification">Portfolio Diversification</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {scenario === 'loan_repayment' && (
          <div className="space-y-2">
            <Label htmlFor="amount">Repayment Amount (QIE)</Label>
            <Input
              id="amount"
              type="number"
              placeholder="100"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
        )}

        {scenario === 'staking' && (
          <>
            <div className="space-y-2">
              <Label htmlFor="amount">Staking Amount (QIE)</Label>
              <Input
                id="amount"
                type="number"
                placeholder="1000"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tier">Staking Tier</Label>
              <Select value={tier} onValueChange={setTier}>
                <SelectTrigger id="tier">
                  <SelectValue placeholder="Select tier" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Bronze</SelectItem>
                  <SelectItem value="2">Silver</SelectItem>
                  <SelectItem value="3">Gold</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        )}

        {scenario === 'transaction_volume' && (
          <div className="space-y-2">
            <Label htmlFor="amount">Volume Increase (QIE)</Label>
            <Input
              id="amount"
              type="number"
              placeholder="5000"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
        )}

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive rounded-md">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <Button onClick={handlePredict} disabled={isLoading || !scenario || !address}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Predicting...
            </>
          ) : (
            'Predict Score Change'
          )}
        </Button>

        {prediction && (
          <div className="mt-6 p-4 bg-muted rounded-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Current Score</span>
              <span className="text-lg font-bold">{prediction.current_score}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Predicted Score</span>
              <span className="text-lg font-bold text-primary">
                {prediction.predicted_score}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Predicted Change</span>
              <span
                className={`text-lg font-bold ${
                  prediction.predicted_change > 0
                    ? 'text-success'
                    : prediction.predicted_change < 0
                    ? 'text-destructive'
                    : 'text-muted-foreground'
                }`}
              >
                {prediction.predicted_change > 0 ? '+' : ''}
                {prediction.predicted_change} points
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Confidence</span>
              <span className="text-sm font-medium">
                {(prediction.confidence_level * 100).toFixed(0)}%
              </span>
            </div>
            <div className="pt-3 border-t border-border">
              <p className="text-sm text-muted-foreground">{prediction.explanation}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

