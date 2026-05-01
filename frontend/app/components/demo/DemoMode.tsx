'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Copy, CheckCircle2, Zap } from 'lucide-react';
import { getNetworkConfig, isMainnet } from '@/lib/config/network';

// Demo addresses (these would come from backend in production)
const DEMO_ADDRESSES = [
  {
    label: 'High Score Wallet',
    address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    score: 850,
    description: 'Wallet with excellent credit history',
  },
  {
    label: 'Medium Score Wallet',
    address: '0x8ba1f109551bD432803012645Hac136c22C177',
    score: 600,
    description: 'Average credit score wallet',
  },
  {
    label: 'Low Score Wallet',
    address: '0x1234567890123456789012345678901234567890',
    score: 350,
    description: 'Wallet with limited history',
  },
];

interface DemoModeProps {
  onSelectAddress?: (address: string) => void;
}

export function DemoMode({ onSelectAddress }: DemoModeProps) {
  const [copiedAddress, setCopiedAddress] = useState<string | null>(null);
  const networkConfig = getNetworkConfig();
  const isMainnetMode = isMainnet(networkConfig);

  const copyToClipboard = (address: string) => {
    navigator.clipboard.writeText(address);
    setCopiedAddress(address);
    setTimeout(() => setCopiedAddress(null), 2000);
  };

  const handleSelectAddress = (address: string) => {
    if (onSelectAddress) {
      onSelectAddress(address);
    } else {
      // Navigate to dashboard with address
      window.location.href = `/dashboard?address=${address}`;
    }
  };

  return (
    <Card className="border-2 border-dashed">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-500" />
          <CardTitle>Quick Demo Mode</CardTitle>
          <Badge variant="secondary">For Evaluators</Badge>
        </div>
        <CardDescription>
          Use these pre-configured addresses to quickly explore AETHER-SCORE features
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isMainnetMode && (
          <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              âš ï¸ <strong>Mainnet Mode:</strong> These are example addresses. Use with caution on mainnet.
            </p>
          </div>
        )}

        <div className="space-y-3">
          {DEMO_ADDRESSES.map((demo) => (
            <div
              key={demo.address}
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold">{demo.label}</span>
                  <Badge variant="outline">Score: {demo.score}</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-2">{demo.description}</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs font-mono bg-muted px-2 py-1 rounded">
                    {demo.address.slice(0, 10)}...{demo.address.slice(-8)}
                  </code>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(demo.address)}
                    className="h-6 px-2"
                  >
                    {copiedAddress === demo.address ? (
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </div>
              <Button
                size="sm"
                onClick={() => handleSelectAddress(demo.address)}
                className="ml-4"
              >
                View Score
              </Button>
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 bg-muted rounded-lg">
          <p className="text-sm font-semibold mb-2">Quick Start Guide:</p>
          <ol className="text-sm space-y-1 list-decimal list-inside text-muted-foreground">
            <li>Select a demo address above</li>
            <li>View credit score and analytics</li>
            <li>Try the score simulator</li>
            <li>Explore loan offers</li>
            <li>Check portfolio and reports</li>
          </ol>
        </div>
      </CardContent>
    </Card>
  );
}


