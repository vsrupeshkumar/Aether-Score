'use client';

import { useState } from 'react';
import { calculateEarlyRepayment, EarlyRepaymentSavings } from '@/app/hooks/useLoans';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, TrendingDown } from 'lucide-react';
import { format } from 'date-fns';

interface EarlyRepaymentCalculatorProps {
  loanId: number;
}

export function EarlyRepaymentCalculator({ loanId }: EarlyRepaymentCalculatorProps) {
  const [earlyDate, setEarlyDate] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [savings, setSavings] = useState<EarlyRepaymentSavings | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    if (!earlyDate) {
      setError('Please select an early payment date');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSavings(null);

    try {
      const result = await calculateEarlyRepayment(loanId, earlyDate);
      if (result) {
        setSavings(result);
      } else {
        setError('Failed to calculate savings');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  // Set default date to tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const defaultDate = format(tomorrow, 'yyyy-MM-dd');

  return (
    <Card>
      <CardHeader>
        <CardTitle>Early Repayment Calculator</CardTitle>
        <CardDescription>
          Calculate how much you could save by repaying your loan early
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="early-date">Early Payment Date</Label>
          <Input
            id="early-date"
            type="date"
            min={defaultDate}
            value={earlyDate}
            onChange={(e) => setEarlyDate(e.target.value)}
          />
        </div>

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive rounded-md">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <Button onClick={handleCalculate} disabled={isLoading || !earlyDate}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Calculating...
            </>
          ) : (
            'Calculate Savings'
          )}
        </Button>

        {savings && (
          <div className="mt-6 p-4 bg-muted rounded-lg space-y-3">
            <div className="flex items-center gap-2 text-success">
              <TrendingDown className="h-5 w-5" />
              <h3 className="font-semibold">Potential Savings</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Total Savings</p>
                <p className="text-2xl font-bold text-success">
                  {savings.savings.toFixed(2)} QIE
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Interest Saved</p>
                <p className="text-xl font-semibold">{savings.interest_saved.toFixed(2)} QIE</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Days Saved</p>
                <p className="text-lg font-semibold">{savings.days_saved} days</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Early Total</p>
                <p className="text-lg font-semibold">{savings.early_total.toFixed(2)} QIE</p>
              </div>
            </div>
            <div className="pt-3 border-t border-border">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Original Total:</span>
                <span className="line-through">{savings.original_total.toFixed(2)} QIE</span>
              </div>
              <div className="flex justify-between text-sm mt-1">
                <span className="text-muted-foreground">Early Total:</span>
                <span className="font-semibold">{savings.early_total.toFixed(2)} QIE</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

