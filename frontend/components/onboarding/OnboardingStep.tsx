'use client';

import { ReactNode } from 'react';
import { onboardingSteps, type OnboardingStep as OnboardingStepType } from '@/lib/onboarding';

interface OnboardingStepProps {
  stepId: string;
  children: ReactNode;
  className?: string;
}

export function OnboardingStep({ stepId, children, className }: OnboardingStepProps) {
  const step = onboardingSteps.find((s) => s.id === stepId);
  
  return (
    <div
      data-onboarding={stepId}
      className={className}
      aria-label={step?.title}
    >
      {children}
    </div>
  );
}

