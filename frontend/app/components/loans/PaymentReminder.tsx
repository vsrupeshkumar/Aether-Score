'use client';

import { useEffect, useState, useMemo } from 'react';
import { useLoans, Loan } from '@/app/hooks/useLoans';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertCircle, Clock, CheckCircle } from 'lucide-react';
import { format, differenceInDays, isPast, isToday } from 'date-fns';
import { useWallet } from '@/app/contexts/WalletContext';
import { NotificationService } from '@/app/lib/notifications';
import Link from 'next/link';

export function PaymentReminder() {
  const { address } = useWallet();
  const { loans } = useLoans(address, 'active');
  const [upcomingPayments, setUpcomingPayments] = useState<Loan[]>([]);
  const [overduePayments, setOverduePayments] = useState<Loan[]>([]);
  const now = useMemo(() => new Date(), []);

  useEffect(() => {
    if (!loans || loans.length === 0) {
      setUpcomingPayments([]);
      setOverduePayments([]);
      return;
    }
    const upcoming: Loan[] = [];
    const overdue: Loan[] = [];

    loans.forEach((loan) => {
      if (!loan.due_date) return;

      const dueDate = new Date(loan.due_date);
      const daysUntilDue = differenceInDays(dueDate, now);

      if (isPast(dueDate) && !isToday(dueDate)) {
        overdue.push(loan);
      } else if (daysUntilDue <= 7 && daysUntilDue >= 0) {
        upcoming.push(loan);
      }
    });

    setUpcomingPayments(upcoming);
    setOverduePayments(overdue);

    // Create notifications for overdue payments
    overdue.forEach((loan) => {
      NotificationService.add({
        type: 'error',
        title: 'Overdue Payment',
        message: `Loan #${loan.loan_id} payment is overdue. Please repay immediately.`,
        actionUrl: `/loans`,
        actionLabel: 'View Loan',
      });
    });

    // Create notifications for upcoming payments
    upcoming.forEach((loan) => {
      const daysUntilDue = differenceInDays(new Date(loan.due_date!), now);
      NotificationService.add({
        type: 'warning',
        title: 'Payment Due Soon',
        message: `Loan #${loan.loan_id} payment is due in ${daysUntilDue} day${daysUntilDue !== 1 ? 's' : ''}.`,
        actionUrl: `/loans`,
        actionLabel: 'View Loan',
      });
    });
  }, [loans]);

  if (upcomingPayments.length === 0 && overduePayments.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payment Reminders</CardTitle>
        <CardDescription>
          {overduePayments.length > 0 && `${overduePayments.length} overdue`}
          {overduePayments.length > 0 && upcomingPayments.length > 0 && ' • '}
          {upcomingPayments.length > 0 && `${upcomingPayments.length} upcoming`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {overduePayments.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2 flex items-center gap-2 text-destructive">
              <AlertCircle className="h-4 w-4" />
              Overdue Payments
            </h3>
            <div className="space-y-2">
              {overduePayments.map((loan) => (
                <div
                  key={loan.loan_id}
                  className="flex items-center justify-between p-3 bg-destructive/10 border border-destructive rounded-lg"
                >
                  <div>
                    <p className="font-semibold">Loan #{loan.loan_id}</p>
                    <p className="text-sm text-muted-foreground">
                      Due: {loan.due_date ? format(new Date(loan.due_date), 'PP') : 'N/A'}
                    </p>
                    <p className="text-sm text-destructive">
                      {loan.due_date
                        ? `${differenceInDays(now, new Date(loan.due_date))} day${differenceInDays(now, new Date(loan.due_date)) !== 1 ? 's' : ''} overdue`
                        : 'Overdue'}
                    </p>
                  </div>
                  <Link href="/loans">
                    <Button variant="destructive" size="sm">
                      Repay Now
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}

        {upcomingPayments.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2 flex items-center gap-2 text-warning">
              <Clock className="h-4 w-4" />
              Upcoming Payments
            </h3>
            <div className="space-y-2">
              {upcomingPayments.map((loan) => {
                const daysUntilDue = loan.due_date
                  ? differenceInDays(new Date(loan.due_date), new Date())
                  : 0;
                return (
                  <div
                    key={loan.loan_id}
                    className="flex items-center justify-between p-3 bg-warning/10 border border-warning rounded-lg"
                  >
                    <div>
                      <p className="font-semibold">Loan #{loan.loan_id}</p>
                      <p className="text-sm text-muted-foreground">
                        Due: {loan.due_date ? format(new Date(loan.due_date), 'PP') : 'N/A'}
                      </p>
                      <p className="text-sm text-warning">
                        {daysUntilDue === 0
                          ? 'Due today'
                          : `${daysUntilDue} day${daysUntilDue !== 1 ? 's' : ''} remaining`}
                      </p>
                    </div>
                    <Link href="/loans">
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                    </Link>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

