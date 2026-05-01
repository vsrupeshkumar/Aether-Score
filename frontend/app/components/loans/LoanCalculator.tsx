"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Button } from "@/app/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs";

export function LoanCalculator() {
  const [principal, setPrincipal] = useState<string>("1000");
  const [interestRate, setInterestRate] = useState<string>("5");
  const [duration, setDuration] = useState<string>("12");
  const [loanType, setLoanType] = useState<"simple" | "compound">("simple");

  const calculateLoan = () => {
    const p = parseFloat(principal) || 0;
    const r = parseFloat(interestRate) || 0;
    const n = parseInt(duration) || 0;

    if (p <= 0 || r < 0 || n <= 0) {
      return {
        monthlyPayment: 0,
        totalInterest: 0,
        totalAmount: 0,
        schedule: [],
      };
    }

    const monthlyRate = r / 100 / 12;
    let monthlyPayment = 0;
    let totalInterest = 0;
    let schedule: any[] = [];

    if (loanType === "compound") {
      // Compound interest with monthly payments
      if (monthlyRate > 0) {
        monthlyPayment = (p * monthlyRate * Math.pow(1 + monthlyRate, n)) / (Math.pow(1 + monthlyRate, n) - 1);
      } else {
        monthlyPayment = p / n;
      }

      totalInterest = monthlyPayment * n - p;

      // Generate amortization schedule
      let balance = p;
      for (let i = 1; i <= n; i++) {
        const interest = balance * monthlyRate;
        const principalPayment = monthlyPayment - interest;
        balance -= principalPayment;

        schedule.push({
          month: i,
          payment: monthlyPayment,
          principal: principalPayment,
          interest: interest,
          balance: Math.max(0, balance),
        });
      }
    } else {
      // Simple interest
      totalInterest = (p * r * n) / 100 / 12;
      monthlyPayment = (p + totalInterest) / n;

      const principalPerMonth = p / n;
      const interestPerMonth = totalInterest / n;
      let balance = p;

      for (let i = 1; i <= n; i++) {
        balance -= principalPerMonth;
        schedule.push({
          month: i,
          payment: monthlyPayment,
          principal: principalPerMonth,
          interest: interestPerMonth,
          balance: Math.max(0, balance),
        });
      }
    }

    return {
      monthlyPayment,
      totalInterest,
      totalAmount: p + totalInterest,
      schedule,
    };
  };

  const result = calculateLoan();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Loan Calculator</CardTitle>
        <CardDescription>Calculate monthly payments and total interest</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="principal">Loan Amount</Label>
            <Input
              id="principal"
              type="number"
              value={principal}
              onChange={(e) => setPrincipal(e.target.value)}
              placeholder="1000"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="interest">Interest Rate (%)</Label>
            <Input
              id="interest"
              type="number"
              value={interestRate}
              onChange={(e) => setInterestRate(e.target.value)}
              placeholder="5"
              step="0.1"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="duration">Duration (months)</Label>
            <Input
              id="duration"
              type="number"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              placeholder="12"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="type">Loan Type</Label>
            <Select value={loanType} onValueChange={(v: "simple" | "compound") => setLoanType(v)}>
              <SelectTrigger id="type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="simple">Simple Interest</SelectItem>
                <SelectItem value="compound">Compound Interest</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 p-4 bg-blue-50 rounded-lg">
          <div>
            <div className="text-sm text-gray-600">Monthly Payment</div>
            <div className="text-2xl font-bold text-blue-600">
              ${result.monthlyPayment.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Total Interest</div>
            <div className="text-2xl font-bold text-green-600">
              ${result.totalInterest.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Total Amount</div>
            <div className="text-2xl font-bold text-purple-600">
              ${result.totalAmount.toFixed(2)}
            </div>
          </div>
        </div>

        {result.schedule.length > 0 && (
          <Tabs defaultValue="summary" className="w-full">
            <TabsList>
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="schedule">Amortization Schedule</TabsTrigger>
            </TabsList>
            <TabsContent value="summary" className="space-y-2">
              <div className="text-sm text-gray-600">
                <p>Principal: ${parseFloat(principal).toFixed(2)}</p>
                <p>Interest Rate: {interestRate}% APR</p>
                <p>Duration: {duration} months</p>
                <p>Type: {loanType === "simple" ? "Simple Interest" : "Compound Interest"}</p>
              </div>
            </TabsContent>
            <TabsContent value="schedule">
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-100">
                    <tr>
                      <th className="text-left p-2">Month</th>
                      <th className="text-right p-2">Payment</th>
                      <th className="text-right p-2">Principal</th>
                      <th className="text-right p-2">Interest</th>
                      <th className="text-right p-2">Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.schedule.map((row) => (
                      <tr key={row.month} className="border-t">
                        <td className="p-2">{row.month}</td>
                        <td className="text-right p-2">${row.payment.toFixed(2)}</td>
                        <td className="text-right p-2">${row.principal.toFixed(2)}</td>
                        <td className="text-right p-2">${row.interest.toFixed(2)}</td>
                        <td className="text-right p-2">${row.balance.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}

