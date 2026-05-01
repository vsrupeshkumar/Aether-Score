import { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '@/lib/api';

export interface TokenHolding {
  token_address: string;
  balance: number;
  balance_raw: string;
  usd_value: number;
  percentage: number;
}

export interface Transaction {
  id: number;
  tx_hash: string;
  tx_type: string;
  block_number: number | null;
  block_timestamp: string | null;
  from_address: string | null;
  to_address: string | null;
  value: number | null;
  gas_used: number | null;
  status: string | null;
  contract_address: string | null;
}

export interface DeFiProtocol {
  protocol: string;
  contract_address: string | null;
  interaction_count: number;
  total_volume: number;
}

export interface RiskFactor {
  factor: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

export interface PortfolioHoldings {
  wallet_address: string;
  holdings: TokenHolding[];
  total_value_usd: number;
}

export interface TransactionHistory {
  wallet_address: string;
  transactions: Transaction[];
  total_count: number;
  page: number;
  limit: number;
}

export interface DeFiActivity {
  wallet_address: string;
  protocols: DeFiProtocol[];
  total_protocols: number;
  total_interactions: number;
  total_volume: number;
}

export interface RiskAssessment {
  wallet_address: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'unknown';
  risk_factors: RiskFactor[];
  recommendations: string[];
  assessment_date: string;
}

export function usePortfolio(address: string | null) {
  const [holdings, setHoldings] = useState<TokenHolding[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [defiActivity, setDefiActivity] = useState<DeFiActivity | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchHoldings = useCallback(async () => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiUrl()}/api/portfolio/${address}/holdings`);
      if (!response.ok) {
        throw new Error(`Failed to fetch holdings: ${response.statusText}`);
      }

      const data: PortfolioHoldings = await response.json();
      setHoldings(data.holdings);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Error fetching holdings:', error);
    } finally {
      setIsLoading(false);
    }
  }, [address]);

  const fetchTransactions = useCallback(async (
    startDate?: string,
    endDate?: string,
    txType?: string,
    limit: number = 100,
    page: number = 1
  ) => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (txType) params.append('tx_type', txType);
      params.append('limit', limit.toString());
      params.append('page', page.toString());

      const response = await fetch(`${getApiUrl()}/api/portfolio/${address}/transactions?${params}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch transactions: ${response.statusText}`);
      }

      const data: TransactionHistory = await response.json();
      setTransactions(data.transactions);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Error fetching transactions:', error);
    } finally {
      setIsLoading(false);
    }
  }, [address]);

  const fetchDeFiActivity = useCallback(async () => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiUrl()}/api/portfolio/${address}/defi-activity`);
      if (!response.ok) {
        throw new Error(`Failed to fetch DeFi activity: ${response.statusText}`);
      }

      const data: DeFiActivity = await response.json();
      setDefiActivity(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Error fetching DeFi activity:', error);
    } finally {
      setIsLoading(false);
    }
  }, [address]);

  const fetchRiskAssessment = useCallback(async () => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiUrl()}/api/portfolio/${address}/risk-assessment`);
      if (!response.ok) {
        throw new Error(`Failed to fetch risk assessment: ${response.statusText}`);
      }

      const data: RiskAssessment = await response.json();
      setRiskAssessment(data);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Error fetching risk assessment:', error);
    } finally {
      setIsLoading(false);
    }
  }, [address]);

  useEffect(() => {
    if (address) {
      fetchHoldings();
      fetchTransactions();
      fetchDeFiActivity();
      fetchRiskAssessment();
    }
  }, [address, fetchHoldings, fetchTransactions, fetchDeFiActivity, fetchRiskAssessment]);

  return {
    holdings,
    transactions,
    defiActivity,
    riskAssessment,
    isLoading,
    error,
    refetchHoldings: fetchHoldings,
    refetchTransactions: fetchTransactions,
    refetchDeFiActivity: fetchDeFiActivity,
    refetchRiskAssessment: fetchRiskAssessment,
  };
}

