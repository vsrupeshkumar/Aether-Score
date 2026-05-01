'use client';

import { LoadingSpinner } from './LoadingSpinner';
import { cn } from '@/app/lib/utils';

interface LoadingOverlayProps {
  isLoading: boolean;
  text?: string;
  className?: string;
  children?: React.ReactNode;
}

export function LoadingOverlay({ isLoading, text, className, children }: LoadingOverlayProps) {
  if (!isLoading) {
    return <>{children}</>;
  }

  return (
    <div className={cn('relative', className)}>
      {children && (
        <div className="opacity-50 pointer-events-none">{children}</div>
      )}
      <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm z-50">
        <LoadingSpinner size="lg" text={text} />
      </div>
    </div>
  );
}

