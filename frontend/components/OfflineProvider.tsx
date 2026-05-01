'use client';

import { useEffect } from 'react';
import { initOfflineDetection, registerServiceWorker } from '@/lib/offline';
import { OfflineIndicator } from '@/components/ui/OfflineIndicator';

export function OfflineProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    initOfflineDetection();
    registerServiceWorker();
  }, []);

  return (
    <>
      {children}
      <OfflineIndicator />
    </>
  );
}

