'use client';

import { useState, useEffect } from "react";
import { Layout } from "@/components/layout/Layout";
import { HeroSection } from "@/components/home/HeroSection";
import { useWallet } from "@/contexts/WalletContext";
import { handleApiError, formatError } from "@/lib/errors";
import { showErrorToast } from "@/components/ui/ErrorToast";
import { isOnboardingCompleted } from "@/lib/onboarding";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";

import { getApiUrl } from '@/lib/api';

export default function Home() {
  const { address, isConnected, connect, isConnecting } = useWallet();
  const [score, setScore] = useState<number>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  const handleConnect = async () => {
    await connect();
  };

  // Check if onboarding should be shown
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setShowOnboarding(!isOnboardingCompleted());
    }
  }, []);

  // Generate score when wallet is connected (but only once)
  useEffect(() => {
    if (address && isConnected && score === undefined) {
      generateScore(address);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [address, isConnected]);

  const generateScore = async (address: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${getApiUrl()}/api/score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ address }),
      });

      if (!response.ok) {
        await handleApiError(response);
        return; // Exit early if there's an error
      }

      const data = await response.json();
      if (data && typeof data.score === 'number') {
        setScore(data.score);
      } else {
        throw new Error('Invalid response format: score not found');
      }
    } catch (error: any) {
      // Check if it's a network error
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new Error('Network error: Unable to connect to the server. Please check your internet connection.');
        setError(networkError);
        showErrorToast({
          error: networkError,
          onRetry: () => generateScore(address),
        });
      } else {
        const formattedError = formatError(error);
        setError(error);
        showErrorToast({
          error,
          onRetry: () => generateScore(address),
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      {showOnboarding && (
        <OnboardingWizard
          onComplete={() => setShowOnboarding(false)}
          onSkip={() => setShowOnboarding(false)}
        />
      )}
      <HeroSection 
        isConnected={isConnected} 
        onConnect={handleConnect}
        score={score}
        isConnecting={isConnecting}
        isLoading={isLoading}
      />
    </Layout>
  );
}

