'use client';

import { useEffect, useState } from 'react';
import { WifiOff, Wifi } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { isOnline, onOfflineStateChange, type OfflineState } from '@/lib/offline';
import { motion, AnimatePresence } from 'framer-motion';

export function OfflineIndicator() {
  const [offlineState, setOfflineState] = useState<OfflineState>({
    isOnline: isOnline(),
    wasOffline: false,
  });

  useEffect(() => {
    const unsubscribe = onOfflineStateChange((state) => {
      setOfflineState(state);
    });

    return unsubscribe;
  }, []);

  return (
    <AnimatePresence>
      {!offlineState.isOnline && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          className="fixed top-0 left-0 right-0 z-50 p-4"
        >
          <Alert variant="destructive" className="max-w-md mx-auto">
            <WifiOff className="h-4 w-4" />
            <AlertDescription>
              You are currently offline. Some features may not be available.
            </AlertDescription>
          </Alert>
        </motion.div>
      )}
      {offlineState.isOnline && offlineState.wasOffline && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          className="fixed top-0 left-0 right-0 z-50 p-4"
        >
          <Alert className="max-w-md mx-auto bg-green-500/10 border-green-500">
            <Wifi className="h-4 w-4 text-green-500" />
            <AlertDescription className="text-green-500">
              Connection restored. You are back online.
            </AlertDescription>
          </Alert>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

