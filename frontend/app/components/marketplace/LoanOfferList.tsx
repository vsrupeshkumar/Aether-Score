"use client";

import { useState, useEffect } from "react";
import { LoanOfferCard } from "./LoanOfferCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getApiUrl } from "@/lib/api";
import { Loader2 } from "lucide-react";

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
}

export function LoanOfferList() {
  const [offers, setOffers] = useState<LoanOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    amount_min: "",
    amount_max: "",
    max_interest_rate: "",
    term_days: "",
  });

  useEffect(() => {
    loadOffers();
  }, []);

  const loadOffers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.amount_min) params.append("amount_min", filters.amount_min);
      if (filters.amount_max) params.append("amount_max", filters.amount_max);
      if (filters.max_interest_rate) params.append("max_interest_rate", filters.max_interest_rate);
      if (filters.term_days) params.append("term_days", filters.term_days);

      const response = await fetch(`${getApiUrl()}/api/marketplace/offers?${params}`);
      if (!response.ok) throw new Error("Failed to fetch offers");
      
      const data = await response.json();
      setOffers(data.offers || []);
    } catch (error) {
      console.error("Error loading offers:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (offerId: number) => {
    // Implementation would connect wallet and call accept endpoint
    console.log("Accept offer:", offerId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Input
          placeholder="Min Amount"
          type="number"
          value={filters.amount_min}
          onChange={(e) => setFilters({ ...filters, amount_min: e.target.value })}
        />
        <Input
          placeholder="Max Amount"
          type="number"
          value={filters.amount_max}
          onChange={(e) => setFilters({ ...filters, amount_max: e.target.value })}
        />
        <Input
          placeholder="Max Interest Rate %"
          type="number"
          value={filters.max_interest_rate}
          onChange={(e) => setFilters({ ...filters, max_interest_rate: e.target.value })}
        />
        <Input
          placeholder="Term (days)"
          type="number"
          value={filters.term_days}
          onChange={(e) => setFilters({ ...filters, term_days: e.target.value })}
        />
      </div>
      <Button onClick={loadOffers}>Apply Filters</Button>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {offers.length === 0 ? (
          <p className="col-span-full text-center text-muted-foreground">
            No offers found
          </p>
        ) : (
          offers.map((offer) => (
            <LoanOfferCard key={offer.id} offer={offer} onAccept={handleAccept} />
          ))
        )}
      </div>
    </div>
  );
}

