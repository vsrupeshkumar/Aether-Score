'use client';

import { useEffect, useState } from 'react';
import { getLoanSchedule, RepaymentSchedule as RepaymentScheduleType } from '@/app/hooks/useLoans';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { format } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';

interface RepaymentScheduleProps {
  loanId: number;
}

export function RepaymentSchedule({ loanId }: RepaymentScheduleProps) {
  const [schedule, setSchedule] = useState<RepaymentScheduleType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSchedule() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getLoanSchedule(loanId);
        setSchedule(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load schedule');
      } finally {
        setIsLoading(false);
      }
    }
    loadSchedule();
  }, [loanId]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Repayment Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center">
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
          <CardTitle>Repayment Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!schedule || schedule.schedule.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Repayment Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No schedule available</p>
        </CardContent>
      </Card>
    );
  }

  const now = new Date();
  const upcomingPayments = schedule.schedule.filter(
    (payment) => new Date(payment.payment_date) > now
  );
  const completedPayments = schedule.schedule.filter(
    (payment) => new Date(payment.payment_date) <= now
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Repayment Schedule</CardTitle>
        <CardDescription>
          Total: {schedule.total_amount.toFixed(2)} QIE ({schedule.total_principal.toFixed(2)} principal +{' '}
          {schedule.total_interest.toFixed(2)} interest)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {upcomingPayments.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Upcoming Payments</h3>
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Payment #</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Principal</TableHead>
                      <TableHead className="text-right">Interest</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead className="text-right">Remaining</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {upcomingPayments.map((payment) => (
                      <TableRow key={payment.payment_number}>
                        <TableCell>{payment.payment_number}</TableCell>
                        <TableCell>{format(new Date(payment.payment_date), 'MMM d, yyyy')}</TableCell>
                        <TableCell className="text-right">{payment.principal.toFixed(2)}</TableCell>
                        <TableCell className="text-right">{payment.interest.toFixed(2)}</TableCell>
                        <TableCell className="text-right font-semibold">
                          {payment.total_payment.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right">
                          {payment.remaining_principal.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {completedPayments.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-2">Completed Payments</h3>
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Payment #</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Principal</TableHead>
                      <TableHead className="text-right">Interest</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {completedPayments.map((payment) => (
                      <TableRow key={payment.payment_number} className="opacity-60">
                        <TableCell>{payment.payment_number}</TableCell>
                        <TableCell>{format(new Date(payment.payment_date), 'MMM d, yyyy')}</TableCell>
                        <TableCell className="text-right">{payment.principal.toFixed(2)}</TableCell>
                        <TableCell className="text-right">{payment.interest.toFixed(2)}</TableCell>
                        <TableCell className="text-right">{payment.total_payment.toFixed(2)}</TableCell>
                        <TableCell>
                          <Badge variant="secondary">Paid</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

