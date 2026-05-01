'use client';

import { useLoans, Loan } from '@/app/hooks/useLoans';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { format } from 'date-fns';
import { useWallet } from '@/app/contexts/WalletContext';
import { ArrowRight, Calendar, DollarSign, Percent } from 'lucide-react';
import Link from 'next/link';

interface LoanListProps {
  status?: string;
  onLoanSelect?: (loan: Loan) => void;
}

export function LoanList({ status, onLoanSelect }: LoanListProps) {
  const { address } = useWallet();
  const { loans, isLoading, error } = useLoans(address, status);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loans</CardTitle>
          <CardDescription>Loading loans...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center">
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
          <CardTitle>Loans</CardTitle>
          <CardDescription>Error loading loans</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error.message}</p>
        </CardContent>
      </Card>
    );
  }

  if (loans.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loans</CardTitle>
          <CardDescription>No loans found</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            {status === 'active'
              ? 'You have no active loans.'
              : 'You have no loans at this time.'}
          </p>
        </CardContent>
      </Card>
    );
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      active: 'default',
      repaid: 'secondary',
      defaulted: 'destructive',
      liquidated: 'destructive',
      pending: 'outline',
    };
    return variants[status] || 'outline';
  };

  return (
    <div className="space-y-4">
      {loans.map((loan) => (
        <Card key={loan.loan_id} className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Loan #{loan.loan_id}</CardTitle>
                <CardDescription>
                  Created {loan.created_at ? format(new Date(loan.created_at), 'PP') : 'N/A'}
                </CardDescription>
              </div>
              <Badge variant={getStatusBadge(loan.status)}>{loan.status}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Amount</p>
                  <p className="font-semibold">{loan.amount.toFixed(2)} QIE</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Percent className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Interest Rate</p>
                  <p className="font-semibold">{loan.interest_rate.toFixed(2)}%</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Term</p>
                  <p className="font-semibold">{loan.term_days} days</p>
                </div>
              </div>
              {loan.due_date && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Due Date</p>
                    <p className="font-semibold">{format(new Date(loan.due_date), 'MMM d')}</p>
                  </div>
                </div>
              )}
            </div>
            {onLoanSelect ? (
              <Button
                variant="outline"
                className="w-full"
                onClick={() => onLoanSelect(loan)}
              >
                View Details <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Link href={`/loans/${loan.loan_id}`}>
                <Button variant="outline" className="w-full">
                  View Details <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

