'use client';

import { useState } from 'react';
import { usePortfolio, Transaction } from '@/app/hooks/usePortfolio';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { format } from 'date-fns';
import { useWallet } from '@/app/contexts/WalletContext';
import { ExternalLink, Download } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { getExplorerTxUrl } from '@/lib/config/network';

export function TransactionHistory() {
  const { address } = useWallet();
  const { transactions, isLoading, error, refetchTransactions } = usePortfolio(address);
  const [searchTerm, setSearchTerm] = useState('');
  const [txTypeFilter, setTxTypeFilter] = useState<string>('all');

  const filteredTransactions = transactions.filter((tx) => {
    const matchesSearch =
      tx.tx_hash.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (tx.from_address && tx.from_address.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (tx.to_address && tx.to_address.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = txTypeFilter === 'all' || tx.tx_type === txTypeFilter;
    return matchesSearch && matchesType;
  });

  const exportToCSV = () => {
    const headers = ['Hash', 'Type', 'From', 'To', 'Value', 'Date', 'Status'];
    const rows = filteredTransactions.map((tx) => [
      tx.tx_hash,
      tx.tx_type,
      tx.from_address || '',
      tx.to_address || '',
      tx.value?.toFixed(4) || '0',
      tx.block_timestamp ? format(new Date(tx.block_timestamp), 'yyyy-MM-dd HH:mm:ss') : '',
      tx.status || 'unknown',
    ]);

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transactions-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
  };

  const getStatusBadge = (status: string | null) => {
    if (!status) return null;
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      success: 'default',
      pending: 'secondary',
      failed: 'destructive',
    };
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Transaction History</CardTitle>
            <CardDescription>
              {filteredTransactions.length} transaction{filteredTransactions.length !== 1 ? 's' : ''}
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={exportToCSV}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder="Search by hash, from, or to address..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
          <Select value={txTypeFilter} onValueChange={setTxTypeFilter}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="transfer">Transfer</SelectItem>
              <SelectItem value="swap">Swap</SelectItem>
              <SelectItem value="approval">Approval</SelectItem>
              <SelectItem value="loan">Loan</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <p className="text-destructive">{error.message}</p>
        ) : filteredTransactions.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">No transactions found</p>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Hash</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTransactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm">
                          {tx.tx_hash.slice(0, 8)}...{tx.tx_hash.slice(-6)}
                        </span>
                        <a
                          href={getExplorerTxUrl(tx.tx_hash)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{tx.tx_type}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {tx.from_address ? `${tx.from_address.slice(0, 6)}...${tx.from_address.slice(-4)}` : '-'}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {tx.to_address ? `${tx.to_address.slice(0, 6)}...${tx.to_address.slice(-4)}` : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {tx.value ? `${tx.value.toFixed(4)} QIE` : '-'}
                    </TableCell>
                    <TableCell>
                      {tx.block_timestamp ? format(new Date(tx.block_timestamp), 'MMM d, yyyy HH:mm') : '-'}
                    </TableCell>
                    <TableCell>{getStatusBadge(tx.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

