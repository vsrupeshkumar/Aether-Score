'use client';

import { useState } from 'react';
import { useWallet } from '@/app/contexts/WalletContext';
import { LoanList } from '@/app/components/loans/LoanList';
import { RepaymentSchedule } from '@/app/components/loans/RepaymentSchedule';
import { EarlyRepaymentCalculator } from '@/app/components/loans/EarlyRepaymentCalculator';
import { Loan, useLoans } from '@/app/hooks/useLoans';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import { DollarSign, Percent, Calendar, AlertCircle } from 'lucide-react';

export default function LoansPage() {
  const { address } = useWallet();
  const { loans: allLoans } = useLoans(address);
  const [selectedLoan, setSelectedLoan] = useState<Loan | null>(null);

  const activeLoans = allLoans.filter((loan) => loan.status === 'active');
  const repaidLoans = allLoans.filter((loan) => loan.status === 'repaid');

  if (!address) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Loan Management</CardTitle>
            <CardDescription>Please connect your wallet to view your loans</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Loan Management</h1>
        <p className="text-muted-foreground">
          View and manage your active loans, repayment schedules, and calculate early repayment savings
        </p>
      </div>

      <Tabs defaultValue="active" className="space-y-4">
        <TabsList>
          <TabsTrigger value="active">
            Active ({activeLoans.length})
          </TabsTrigger>
          <TabsTrigger value="all">All Loans ({allLoans.length})</TabsTrigger>
          <TabsTrigger value="repaid">Repaid ({repaidLoans.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-6">
          {activeLoans.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground text-center">
                  You have no active loans at this time.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <LoanList status="active" onLoanSelect={setSelectedLoan} />
              {selectedLoan && (
                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle>Loan #{selectedLoan.loan_id} Details</CardTitle>
                          <CardDescription>
                            Created {selectedLoan.created_at ? format(new Date(selectedLoan.created_at), 'PP') : 'N/A'}
                          </CardDescription>
                        </div>
                        <Badge>{selectedLoan.status}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-xs text-muted-foreground">Amount</p>
                            <p className="font-semibold">{selectedLoan.amount.toFixed(2)} QIE</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Percent className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-xs text-muted-foreground">Interest Rate</p>
                            <p className="font-semibold">{selectedLoan.interest_rate.toFixed(2)}%</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-xs text-muted-foreground">Term</p>
                            <p className="font-semibold">{selectedLoan.term_days} days</p>
                          </div>
                        </div>
                        {selectedLoan.due_date && (
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="text-xs text-muted-foreground">Due Date</p>
                              <p className="font-semibold">{format(new Date(selectedLoan.due_date), 'MMM d')}</p>
                            </div>
                          </div>
                        )}
                      </div>
                      {selectedLoan.due_date && new Date(selectedLoan.due_date) < new Date() && (
                        <div className="mt-4 p-3 bg-destructive/10 border border-destructive rounded-md flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 text-destructive" />
                          <p className="text-sm text-destructive">This loan is overdue</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                  <RepaymentSchedule loanId={selectedLoan.loan_id} />
                  <EarlyRepaymentCalculator loanId={selectedLoan.loan_id} />
                </div>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="all">
          <LoanList onLoanSelect={setSelectedLoan} />
        </TabsContent>

        <TabsContent value="repaid">
          <LoanList status="repaid" />
        </TabsContent>
      </Tabs>
    </div>
  );
}

