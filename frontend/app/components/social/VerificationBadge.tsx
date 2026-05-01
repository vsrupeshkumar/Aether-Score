'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, ExternalLink, Shield } from 'lucide-react';
import { getApiUrl } from '@/lib/api';

interface VerificationBadgeProps {
  address: string;
}

export function VerificationBadge({ address }: VerificationBadgeProps) {
  const [proof, setProof] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProof = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/social/verify/${address}`);
        if (response.ok) {
          const data = await response.json();
          setProof(data);
        }
      } catch (error) {
        console.error('Error fetching verification proof:', error);
      } finally {
        setLoading(false);
      }
    };

    if (address) {
      fetchProof();
    }
  }, [address]);

  if (loading) {
    return <div className="animate-pulse bg-gray-200 rounded-lg w-48 h-16" />;
  }

  if (!proof?.verified) {
    return null;
  }

  return (
    <div className="inline-flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-4 py-2">
      <CheckCircle className="w-5 h-5 text-green-600" />
      <div className="flex-1">
        <div className="text-sm font-semibold text-green-900">Verified On-Chain</div>
        {proof.token_id && (
          <div className="text-xs text-green-700">Token ID: {proof.token_id}</div>
        )}
      </div>
      {proof.explorer_link && (
        <a
          href={proof.explorer_link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-green-600 hover:text-green-800"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      )}
    </div>
  );
}

