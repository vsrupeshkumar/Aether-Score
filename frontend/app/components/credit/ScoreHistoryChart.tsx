'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts';
import { format, parseISO, subDays } from 'date-fns';
import { useScoreHistory, ScoreHistoryEntry } from '@/app/hooks/useScoreHistory';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useState } from 'react';

interface ScoreHistoryChartProps {
  address: string | null;
}

const TIME_RANGES = {
  '7d': { days: 7, label: '7 Days' },
  '30d': { days: 30, label: '30 Days' },
  '90d': { days: 90, label: '90 Days' },
  '1y': { days: 365, label: '1 Year' },
  'all': { days: Infinity, label: 'All Time' },
};

function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
        <p className="text-sm font-medium mb-2">{format(parseISO(label), 'PPp')}</p>
        <p className="text-lg font-bold text-primary">
          Score: {payload[0].value}
        </p>
        {data.previous_score !== null && (
          <p className="text-xs text-muted-foreground mt-1">
            Change: {data.score - data.previous_score > 0 ? '+' : ''}
            {data.score - data.previous_score} points
          </p>
        )}
        {data.explanation && (
          <p className="text-xs text-muted-foreground mt-2 max-w-xs">
            {data.explanation}
          </p>
        )}
      </div>
    );
  }
  return null;
}

export function ScoreHistoryChart({ address }: ScoreHistoryChartProps) {
  const { history, trends, isLoading, error } = useScoreHistory(address);
  const [timeRange, setTimeRange] = useState<keyof typeof TIME_RANGES>('30d');

  const chartData = useMemo(() => {
    if (!history || history.length === 0) return [];

    const range = TIME_RANGES[timeRange];
    const cutoffDate = range.days === Infinity 
      ? null 
      : subDays(new Date(), range.days);

    const filtered = cutoffDate
      ? history.filter(entry => {
          if (!entry.computed_at) return false;
          return parseISO(entry.computed_at) >= cutoffDate;
        })
      : history;

    // Sort by date ascending for chart
    return filtered
      .map(entry => ({
        date: entry.computed_at || new Date().toISOString(),
        score: entry.score,
        previous_score: entry.previous_score,
        explanation: entry.explanation,
        change_reason: entry.change_reason,
      }))
      .sort((a, b) => parseISO(a.date).getTime() - parseISO(b.date).getTime());
  }, [history, timeRange]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Score History</CardTitle>
          <CardDescription>Loading score history...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Score History</CardTitle>
          <CardDescription>Error loading score history</CardDescription>
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
          <CardTitle>Score History</CardTitle>
          <CardDescription>No score history available</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Score history will appear here once scores are computed.
          </p>
        </CardContent>
      </Card>
    );
  }

  const minScore = Math.min(...chartData.map(d => d.score));
  const maxScore = Math.max(...chartData.map(d => d.score));
  const yAxisDomain = [
    Math.max(0, Math.floor(minScore / 100) * 100 - 50),
    Math.min(1000, Math.ceil(maxScore / 100) * 100 + 50),
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Score History</CardTitle>
            <CardDescription>
              {trends && (
                <span className="flex items-center gap-2 mt-1">
                  <span>
                    {trends.trend_direction === 'up' && '📈'}
                    {trends.trend_direction === 'down' && '📉'}
                    {trends.trend_direction === 'stable' && '➡️'}
                  </span>
                  <span>
                    {trends.change_30d > 0 ? '+' : ''}
                    {trends.change_30d} points ({trends.change_30d_percent > 0 ? '+' : ''}
                    {trends.change_30d_percent.toFixed(1)}%) in last 30 days
                  </span>
                </span>
              )}
            </CardDescription>
          </div>
          <Select value={timeRange} onValueChange={(value) => setTimeRange(value as keyof typeof TIME_RANGES)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(TIME_RANGES).map(([key, { label }]) => (
                <SelectItem key={key} value={key}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
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
            <YAxis
              domain={yAxisDomain}
              stroke="hsl(var(--muted-foreground))"
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={500} stroke="hsl(var(--muted))" strokeDasharray="2 2" />
            <Area
              type="monotone"
              dataKey="score"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              fill="url(#scoreGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

