'use client';

import { toast } from 'sonner';
import { formatError, isRetryableError } from '@/lib/errors';
import { RefreshCw } from 'lucide-react';

interface ErrorToastOptions {
  error: unknown;
  onRetry?: () => void;
  duration?: number;
}

/**
 * Show error toast notification
 */
export function showErrorToast({ error, onRetry, duration = 5000 }: ErrorToastOptions) {
  const formattedError = formatError(error);
  const canRetry = isRetryableError(error) && onRetry;

  toast.error(formattedError.message, {
    duration,
    action: canRetry
      ? {
          label: 'Retry',
          onClick: onRetry,
        }
      : undefined,
  });
}

/**
 * Show success toast notification
 */
export function showSuccessToast(message: string, duration = 3000) {
  toast.success(message, { duration });
}

/**
 * Show info toast notification
 */
export function showInfoToast(message: string, duration = 3000) {
  toast.info(message, { duration });
}

/**
 * Show warning toast notification
 */
export function showWarningToast(message: string, duration = 4000) {
  toast.warning(message, { duration });
}

