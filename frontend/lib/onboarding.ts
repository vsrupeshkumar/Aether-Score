/**
 * Onboarding state management
 */

const ONBOARDING_STORAGE_KEY = 'AETHER-SCORE_onboarding_completed';
const ONBOARDING_STEPS_KEY = 'AETHER-SCORE_onboarding_steps';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  target?: string; // CSS selector for element to highlight
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export const onboardingSteps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to AETHER-SCORE',
    description: 'Get your AI-powered credit score on the QIE blockchain',
  },
  {
    id: 'connect-wallet',
    title: 'Connect Your Wallet',
    description: 'Connect your MetaMask or QIE Wallet to get started',
    target: '[data-onboarding="connect-wallet"]',
    position: 'bottom',
  },
  {
    id: 'generate-score',
    title: 'Generate Credit Score',
    description: 'Click here to generate your credit score based on your on-chain activity',
    target: '[data-onboarding="generate-score"]',
    position: 'bottom',
  },
  {
    id: 'dashboard',
    title: 'View Dashboard',
    description: 'See your credit score, risk band, and staking information',
    target: '[data-onboarding="dashboard"]',
    position: 'right',
  },
];

/**
 * Check if onboarding is completed
 */
export function isOnboardingCompleted(): boolean {
  if (typeof window === 'undefined') {
    return true;
  }
  
  return localStorage.getItem(ONBOARDING_STORAGE_KEY) === 'true';
}

/**
 * Mark onboarding as completed
 */
export function completeOnboarding(): void {
  if (typeof window === 'undefined') {
    return;
  }
  
  localStorage.setItem(ONBOARDING_STORAGE_KEY, 'true');
}

/**
 * Reset onboarding (for testing)
 */
export function resetOnboarding(): void {
  if (typeof window === 'undefined') {
    return;
  }
  
  localStorage.removeItem(ONBOARDING_STORAGE_KEY);
  localStorage.removeItem(ONBOARDING_STEPS_KEY);
}

/**
 * Get completed steps
 */
export function getCompletedSteps(): string[] {
  if (typeof window === 'undefined') {
    return [];
  }
  
  const stored = localStorage.getItem(ONBOARDING_STEPS_KEY);
  return stored ? JSON.parse(stored) : [];
}

/**
 * Mark step as completed
 */
export function completeStep(stepId: string): void {
  if (typeof window === 'undefined') {
    return;
  }
  
  const completed = getCompletedSteps();
  if (!completed.includes(stepId)) {
    completed.push(stepId);
    localStorage.setItem(ONBOARDING_STEPS_KEY, JSON.stringify(completed));
  }
}

/**
 * Check if step is completed
 */
export function isStepCompleted(stepId: string): boolean {
  return getCompletedSteps().includes(stepId);
}


