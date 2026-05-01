'use client';

import { AlertCircle, X, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatError, isRetryableError } from '@/lib/errors';
import { useState } from 'react';

interface ErrorAlertProps {
  error: unknown;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  title?: string;
}

export function ErrorAlert({
  error,
  onRetry,
  onDismiss,
  className = '',
  title,
}: ErrorAlertProps) {
  const [dismissed, setDismissed] = useState(false);
  const formattedError = formatError(error);
  const canRetry = isRetryableError(error) && onRetry;

  if (dismissed) {
    return null;
  }

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title || 'Error'}</AlertTitle>
      <AlertDescription className="flex items-center justify-between gap-4">
        <span>{formattedError.message}</span>
        <div className="flex items-center gap-2">
          {canRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="h-8"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}

