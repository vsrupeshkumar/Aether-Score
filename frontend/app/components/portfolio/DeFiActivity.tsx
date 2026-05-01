'use client';

import { usePortfolio } from '@/app/hooks/usePortfolio';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useWallet } from '@/app/contexts/WalletContext';
import { Loader2, ExternalLink } from 'lucide-react';
import { getExplorerAddressUrl } from '@/lib/config/network';

export function DeFiActivity() {
  const { address } = useWallet();
  const { defiActivity, isLoading, error } = usePortfolio(address);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DeFi Activity</CardTitle>
          <CardDescription>Loading DeFi activity...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
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
          <CardTitle>DeFi Activity</CardTitle>
          <CardDescription>Error loading DeFi activity</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error.message}</p>
        </CardContent>
      </Card>
    );
  }

  if (!defiActivity || defiActivity.protocols.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DeFi Activity</CardTitle>
          <CardDescription>No DeFi activity found</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            DeFi protocol interactions will appear here once detected.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>DeFi Activity</CardTitle>
        <CardDescription>
          {defiActivity.total_protocols} protocol{defiActivity.total_protocols !== 1 ? 's' : ''} •{' '}
          {defiActivity.total_interactions} interaction{defiActivity.total_interactions !== 1 ? 's' : ''} •{' '}
          {defiActivity.total_volume.toFixed(2)} QIE total volume
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {defiActivity.protocols.map((protocol, index) => (
            <div
              key={protocol.contract_address || index}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold">{protocol.protocol}</h3>
                  {protocol.contract_address && (
                    <a
                      href={getExplorerAddressUrl(protocol.contract_address)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{protocol.interaction_count} interaction{protocol.interaction_count !== 1 ? 's' : ''}</span>
                  <span>{protocol.total_volume.toFixed(2)} QIE volume</span>
                </div>
              </div>
              <Badge variant="outline">{protocol.protocol}</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

