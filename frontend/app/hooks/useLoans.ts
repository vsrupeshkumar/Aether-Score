import { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '@/lib/api';

export interface Loan {
  id?: number;
  loan_id: number;
  wallet_address: string;
  amount: number;
  interest_rate: number;
  term_days: number;
  status: string;
  collateral_amount?: number;
  collateral_token?: string;
  created_at?: string;
  due_date?: string;
  repaid_at?: string;
  tx_hash?: string;
}

export interface RepaymentScheduleEntry {
  payment_number: number;
  payment_date: string;
  principal: number;
  interest: number;
  total_payment: number;
  remaining_principal: number;
}

export interface RepaymentSchedule {
  loan_id: number;
  schedule: RepaymentScheduleEntry[];
  total_principal: number;
  total_interest: number;
  total_amount: number;
}

export interface EarlyRepaymentSavings {
  savings: number;
  interest_saved: number;
  days_saved: number;
  original_total: number;
  early_total: number;
  original_interest: number;
  early_interest: number;
}

export function useLoans(address: string | null, status?: string) {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchLoans = useCallback(async () => {
    if (!address) return;

    setIsLoading(true);
    setError(null);

    try {
      const url = status
        ? `${getApiUrl()}/api/loans/${address}?status=${status}`
        : `${getApiUrl()}/api/loans/${address}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch loans: ${response.statusText}`);
      }

      const data = await response.json();
      setLoans(data.loans || []);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Error fetching loans:', error);
    } finally {
      setIsLoading(false);
    }
  }, [address, status]);

  useEffect(() => {
    if (address) {
      fetchLoans();
      // Refresh every 30 seconds
      const interval = setInterval(fetchLoans, 30000);
      return () => clearInterval(interval);
    }
  }, [address, status, fetchLoans]);

  return {
    loans,
    isLoading,
    error,
    refetch: fetchLoans,
  };
}

export async function getLoanSchedule(loanId: number): Promise<RepaymentSchedule | null> {
  try {
    const response = await fetch(`${getApiUrl()}/api/loans/${loanId}/schedule`);
    if (!response.ok) {
      throw new Error(`Failed to fetch loan schedule: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching loan schedule:', error);
    return null;
  }
}

export async function calculateEarlyRepayment(
  loanId: number,
  earlyPaymentDate: string
): Promise<EarlyRepaymentSavings | null> {
  try {
    const response = await fetch(`${getApiUrl()}/api/loans/calculate-early-repayment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        loan_id: loanId,
        early_payment_date: earlyPaymentDate,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to calculate early repayment: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error calculating early repayment:', error);
    return null;
  }
}

export async function compareLoans(loan1: Loan, loan2: Loan) {
  try {
    const response = await fetch(`${getApiUrl()}/api/loans/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        loan1,
        loan2,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to compare loans: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error comparing loans:', error);
    return null;
  }
}

