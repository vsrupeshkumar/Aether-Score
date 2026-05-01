/**
 * Offline detection and management utilities
 */

export interface OfflineState {
  isOnline: boolean;
  wasOffline: boolean;
}

let offlineState: OfflineState = {
  isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
  wasOffline: false,
};

const listeners: Array<(state: OfflineState) => void> = [];

/**
 * Check if currently online
 */
export function isOnline(): boolean {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

/**
 * Subscribe to online/offline state changes
 */
export function onOfflineStateChange(callback: (state: OfflineState) => void): () => void {
  listeners.push(callback);
  
  // Return unsubscribe function
  return () => {
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  };
}

/**
 * Notify all listeners of state change
 */
function notifyListeners() {
  const wasOffline = !offlineState.isOnline && navigator.onLine;
  offlineState = {
    isOnline: navigator.onLine,
    wasOffline,
  };
  
  listeners.forEach((listener) => listener(offlineState));
}

/**
 * Initialize offline detection
 */
export function initOfflineDetection() {
  if (typeof window === 'undefined') {
    return;
  }

  window.addEventListener('online', () => {
    notifyListeners();
  });

  window.addEventListener('offline', () => {
    notifyListeners();
  });

  // Initial state
  notifyListeners();
}

/**
 * Register service worker
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });

    console.log('Service Worker registered:', registration);
    return registration;
  } catch (error) {
    console.error('Service Worker registration failed:', error);
    return null;
  }
}

/**
 * Get cached API response
 */
export async function getCachedResponse(url: string): Promise<Response | null> {
  if (typeof caches === 'undefined') {
    return null;
  }

  try {
    const cache = await caches.open('AETHER-SCORE-api-v1');
    return (await cache.match(url)) || null;
  } catch (error) {
    console.error('Error getting cached response:', error);
    return null;
  }
}

/**
 * Cache API response
 */
export async function cacheResponse(url: string, response: Response): Promise<void> {
  if (typeof caches === 'undefined') {
    return;
  }

  try {
    const cache = await caches.open('AETHER-SCORE-api-v1');
    await cache.put(url, response.clone());
  } catch (error) {
    console.error('Error caching response:', error);
  }
}


