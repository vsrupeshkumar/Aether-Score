'use client';

import { useMemo } from 'react';
import { usePortfolio } from '@/app/hooks/usePortfolio';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format, parseISO, startOfDay } from 'date-fns';
import { useWallet } from '@/app/contexts/WalletContext';
import { Loader2 } from 'lucide-react';

export function TransactionChart() {
  const { address } = useWallet();
  const { transactions, isLoading, error } = usePortfolio(address);

  const chartData = useMemo(() => {
    if (!transactions || transactions.length === 0) return [];

    // Group transactions by day
    const dailyData: Record<string, { date: string; volume: number; count: number }> = {};

    transactions.forEach((tx) => {
      if (!tx.block_timestamp) return;
      const date = startOfDay(parseISO(tx.block_timestamp));
      const dateKey = format(date, 'yyyy-MM-dd');

      if (!dailyData[dateKey]) {
        dailyData[dateKey] = { date: dateKey, volume: 0, count: 0 };
      }

      dailyData[dateKey].volume += tx.value || 0;
      dailyData[dateKey].count += 1;
    });

    // Convert to array and sort by date
    return Object.values(dailyData)
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((item) => ({
        date: item.date,
        volume: item.volume,
        count: item.count,
      }));
  }, [transactions]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction Volume</CardTitle>
          <CardDescription>Loading transaction data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction Volume</CardTitle>
          <CardDescription>Error loading transaction data</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error.message}</p>
        </CardContent>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction Volume</CardTitle>
          <CardDescription>No transaction data available</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Transaction volume chart will appear here once transactions are tracked.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transaction Volume Over Time</CardTitle>
        <CardDescription>
          Daily transaction volume and count
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
            <XAxis
              dataKey="date"
              tickFormatter={(value) => format(parseISO(value), 'MMM d')}
              stroke="hsl(var(--muted-foreground))"
            />
            <YAxis stroke="hsl(var(--muted-foreground))" />
            <Tooltip
              labelFormatter={(value) => format(parseISO(value), 'PP')}
              formatter={(value: number) => [value.toFixed(4), 'Volume (QIE)']}
            />
            <Area
              type="monotone"
              dataKey="volume"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              fill="url(#volumeGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

