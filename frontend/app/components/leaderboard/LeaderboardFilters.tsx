'use client';

import { Calendar, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface LeaderboardFiltersProps {
  category: string;
  onCategoryChange: (category: string) => void;
}

export function LeaderboardFilters({ category, onCategoryChange }: LeaderboardFiltersProps) {
  const categories = [
    { value: 'all_time', label: 'All-Time' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'weekly', label: 'Weekly' },
  ];

  return (
    <div className="flex items-center gap-2 mb-4">
      <Filter className="w-4 h-4 text-gray-500" />
      <span className="text-sm font-medium">Filter:</span>
      {categories.map((cat) => (
        <Button
          key={cat.value}
          variant={category === cat.value ? 'default' : 'outline'}
          size="sm"
          onClick={() => onCategoryChange(cat.value)}
        >
          {cat.label}
        </Button>
      ))}
    </div>
  );
}

