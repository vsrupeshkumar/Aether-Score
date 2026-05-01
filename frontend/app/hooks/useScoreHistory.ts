import { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '@/lib/api';

export interface ScoreHistoryEntry {
  id: number;
  score: number;
  risk_band: number;
  previous_score: number | null;
  explanation: string | null;
  change_reason: string | null;
  computed_at: string | null;
}

export interface ScoreHistoryData {
  wallet_address: string;
  history: ScoreHistoryEntry[];
  total_count: number;
}

export interface ScoreTrends {
  wallet_address: string;
  current_score: number;
  change_30d: number;
  change_30d_percent: number;
  trend_direction: 'up' | 'down' | 'stable';
  average_score: number;
  highest_score: number;
  lowest_score: number;
}

export function useScoreHistory(address: string | null) {
  const [history, setHistory] = useState<ScoreHistoryEntry[]>([]);
  const [trends, setTrends] = useState<ScoreTrends | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchHistory = useCallback(async (
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ) => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('limit', limit.toString());

      const response = await fetch(`${getApiUrl()}/api/score/${address}/history?${params}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch score history: ${response.statusText}`);
      }

      const data: ScoreHistoryData = await response.json();
      setHistory(data.history);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Error fetching score history:', error);
    } finally {
      setIsLoading(false);
    }
  }, [address]);

  const fetchTrends = useCallback(async () => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiUrl()}/api/score/${address}/trends`);
      if (!response.ok) {
        throw new Error(`Failed to fetch score trends: ${response.statusText}`);
      }

      const data: ScoreTrends = await response.json();
      setTrends(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Error fetching score trends:', error);
    } finally {
      setIsLoading(false);
    }
  }, [address]);

  useEffect(() => {
    if (address) {
      fetchHistory();
      fetchTrends();
    }
  }, [address, fetchHistory, fetchTrends]);

  return {
    history,
    trends,
    isLoading,
    error,
    refetch: fetchHistory,
    refetchTrends: fetchTrends,
  };
}

