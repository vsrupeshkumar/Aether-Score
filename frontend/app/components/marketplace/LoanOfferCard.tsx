"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrendingDown, Clock, Shield, CheckCircle2 } from "lucide-react";

interface LoanOffer {
  id: number;
  lender_address: string;
  amount_min: number;
  amount_max: number;
  interest_rate: number;
  term_days_min: number;
  term_days_max: number;
  collateral_required: boolean;
  status: string;
  created_at?: string;
}

interface LoanOfferCardProps {
  offer: LoanOffer;
  onAccept?: (offerId: number) => void;
}

export function LoanOfferCard({ offer, onAccept }: LoanOfferCardProps) {
  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg">Loan Offer #{offer.id}</CardTitle>
          <Badge variant={offer.status === 'active' ? 'default' : 'secondary'}>
            {offer.status}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Lender: {formatAddress(offer.lender_address)}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Amount Range</p>
            <p className="font-semibold">
              {offer.amount_min.toLocaleString()} - {offer.amount_max.toLocaleString()} QIE
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Interest Rate</p>
            <p className="font-semibold flex items-center gap-1">
              <TrendingDown className="w-4 h-4" />
              {offer.interest_rate}% APR
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Term</p>
            <p className="font-semibold flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {offer.term_days_min} - {offer.term_days_max} days
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Collateral</p>
            <p className="font-semibold flex items-center gap-1">
              {offer.collateral_required ? (
                <>
                  <Shield className="w-4 h-4" />
                  Required
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  Not Required
                </>
              )}
            </p>
          </div>
        </div>
        {onAccept && offer.status === 'active' && (
          <Button onClick={() => onAccept(offer.id)} className="w-full">
            Accept Offer
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

