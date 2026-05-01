'use client';

import { useState, useEffect } from 'react';
import { Twitter, Linkedin, Facebook, Share2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getApiUrl } from '@/lib/api';

interface ShareButtonsProps {
  address: string;
  onShare?: (platform: string) => void;
}

export function ShareButtons({ address, onShare }: ShareButtonsProps) {
  const [shareLinks, setShareLinks] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchShareLinks = async () => {
      if (!address) return;
      
      setLoading(true);
      try {
        const response = await fetch(`${getApiUrl()}/api/social/share-links/${address}`);
        if (response.ok) {
          const data = await response.json();
          setShareLinks(data);
        }
      } catch (error) {
        console.error('Error fetching share links:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchShareLinks();
  }, [address]);

  const handleShare = (platform: string, url: string) => {
    window.open(url, '_blank', 'width=600,height=400');
    onShare?.(platform);
    
    // Record share event
    fetch(`${getApiUrl()}/api/social/share`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        address,
        share_type: platform,
        share_url: url,
      }),
    }).catch(console.error);
  };

  if (loading) {
    return <div className="flex gap-2"><div className="animate-pulse bg-gray-200 rounded w-12 h-10" /></div>;
  }

  const platforms = shareLinks?.platforms || {};

  return (
    <div className="flex gap-2 flex-wrap">
      {platforms.twitter && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleShare('twitter', platforms.twitter.share_url)}
          className="flex items-center gap-2"
        >
          <Twitter className="w-4 h-4" />
          Twitter
        </Button>
      )}
      
      {platforms.linkedin && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleShare('linkedin', platforms.linkedin.share_url)}
          className="flex items-center gap-2"
        >
          <Linkedin className="w-4 h-4" />
          LinkedIn
        </Button>
      )}
      
      {platforms.facebook && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleShare('facebook', platforms.facebook.share_url)}
          className="flex items-center gap-2"
        >
          <Facebook className="w-4 h-4" />
          Facebook
        </Button>
      )}

      {navigator.share && (
        <Button
          variant="outline"
          size="sm"
          onClick={async () => {
            try {
              await navigator.share({
                title: 'My AETHER-SCORE Credit Score',
                text: `Check out my AETHER-SCORE credit score!`,
                url: shareLinks?.badge_data?.badge_url || window.location.href,
              });
              onShare?.('native');
            } catch (error) {
              console.error('Error sharing:', error);
            }
          }}
          className="flex items-center gap-2"
        >
          <Share2 className="w-4 h-4" />
          Share
        </Button>
      )}
    </div>
  );
}


