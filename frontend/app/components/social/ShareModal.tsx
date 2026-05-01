'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { ScoreBadge } from './ScoreBadge';
import { ShareButtons } from './ShareButtons';
import { VerificationBadge } from './VerificationBadge';

interface ShareModalProps {
  address: string;
  score?: number;
  riskBand?: number;
  isOpen: boolean;
  onClose: () => void;
}

export function ShareModal({ address, score, riskBand, isOpen, onClose }: ShareModalProps) {
  const [badgeStyle, setBadgeStyle] = useState<'minimal' | 'detailed' | 'verified'>('verified');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-2xl font-bold mb-4">Share Your Credit Score</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Badge Style</label>
          <select
            value={badgeStyle}
            onChange={(e) => setBadgeStyle(e.target.value as any)}
            className="w-full border rounded-lg px-3 py-2"
          >
            <option value="minimal">Minimal</option>
            <option value="detailed">Detailed</option>
            <option value="verified">Verified</option>
          </select>
        </div>

        <div className="mb-6">
          <ScoreBadge address={address} style={badgeStyle} score={score} riskBand={riskBand} />
        </div>

        <div className="mb-4">
          <VerificationBadge address={address} />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Share on</label>
          <ShareButtons address={address} />
        </div>

        <button
          onClick={onClose}
          className="w-full bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700"
        >
          Close
        </button>
      </div>
    </div>
  );
}

