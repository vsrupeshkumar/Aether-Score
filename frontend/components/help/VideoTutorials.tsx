'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Play } from 'lucide-react';

const tutorials = [
  {
    id: 1,
    title: 'Getting Started with AETHER-SCORE',
    description: 'Learn how to connect your wallet and generate your first credit score',
    duration: '5:23',
    thumbnail: '/tutorials/getting-started.jpg',
  },
  {
    id: 2,
    title: 'Understanding Credit Scores',
    description: 'Learn how credit scores are calculated and what factors affect them',
    duration: '7:45',
    thumbnail: '/tutorials/credit-scores.jpg',
  },
  {
    id: 3,
    title: 'Staking NCRD Tokens',
    description: 'Learn how to stake tokens to boost your credit tier',
    duration: '4:12',
    thumbnail: '/tutorials/staking.jpg',
  },
  {
    id: 4,
    title: 'Using NeuroLend',
    description: 'Learn how to create and manage loans using AI negotiation',
    duration: '6:30',
    thumbnail: '/tutorials/lending.jpg',
  },
];

export function VideoTutorials() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Video Tutorials</CardTitle>
        <CardDescription>
          Step-by-step video guides to help you get the most out of AETHER-SCORE
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid md:grid-cols-2 gap-4">
          {tutorials.map((tutorial) => (
            <div
              key={tutorial.id}
              className="relative group cursor-pointer rounded-lg overflow-hidden border border-border hover:border-primary transition-colors"
            >
              <div className="aspect-video bg-muted flex items-center justify-center">
                <Play className="h-12 w-12 text-primary opacity-70 group-hover:opacity-100 transition-opacity" />
              </div>
              <div className="p-4">
                <h3 className="font-semibold mb-1">{tutorial.title}</h3>
                <p className="text-sm text-muted-foreground mb-2">{tutorial.description}</p>
                <span className="text-xs text-muted-foreground">{tutorial.duration}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}


