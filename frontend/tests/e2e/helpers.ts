import { Page } from '@playwright/test';

/**
 * Helper functions for E2E tests
 */

export async function connectWallet(page: Page) {
  const connectButton = page.getByRole('button', { name: /connect wallet/i });
  await connectButton.click();
  
  // Wait for connection (this would need to be adjusted based on actual implementation)
  // For now, we just wait a bit
  await page.waitForTimeout(1000);
}

export async function generateScore(page: Page, address: string) {
  // Navigate to dashboard
  await page.goto('/dashboard');
  
  // Find and click generate button
  const generateButton = page.getByRole('button', { name: /generate|create.*score/i });
  if (await generateButton.count() > 0) {
    await generateButton.click();
    await page.waitForTimeout(2000); // Wait for API call
  }
}

export async function sendChatMessage(page: Page, message: string) {
  const chatInput = page.locator('input[type="text"], textarea').first();
  const sendButton = page.getByRole('button', { name: /send|submit/i });
  
  if (await chatInput.count() > 0) {
    await chatInput.fill(message);
    if (await sendButton.count() > 0) {
      await sendButton.click();
      await page.waitForTimeout(1000); // Wait for response
    }
  }
}

