/**
 * API URL configuration
 * Automatically detects environment and uses appropriate backend URL
 */

// Production backend URL
const PRODUCTION_API_URL = 'https://AETHER-SCORE-backend.onrender.com';

// Development backend URL
const DEVELOPMENT_API_URL = 'http://localhost:8000';

/**
 * Get the API URL based on environment
 * - Uses NEXT_PUBLIC_API_URL if explicitly set (highest priority)
 * - Uses production URL if deployed on Vercel or in production
 * - Falls back to localhost for local development
 */
export function getApiUrl(): string {
  // Priority 1: Explicitly set environment variable (for custom deployments)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // Priority 2: Check if we're in a browser (client-side)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // Check if we're on localhost
    const isLocalhost = hostname === 'localhost' || 
                       hostname === '127.0.0.1' ||
                       hostname.startsWith('192.168.') ||
                       hostname.startsWith('10.') ||
                       hostname.endsWith('.local');
    
    if (isLocalhost) {
      return DEVELOPMENT_API_URL;
    }
    // Production (Vercel, custom domain, etc.)
    return PRODUCTION_API_URL;
  }

  // Priority 3: Server-side rendering - check NODE_ENV
  if (process.env.NODE_ENV === 'production' || process.env.VERCEL === '1') {
    return PRODUCTION_API_URL;
  }

  // Default: development mode
  return DEVELOPMENT_API_URL;
}


