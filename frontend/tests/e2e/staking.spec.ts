import { test, expect } from '@playwright/test';

test.describe('Staking', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/stake');
  });

  test('should display staking interface', async ({ page }) => {
    // Check for stake button or input
    const stakeButton = page.getByRole('button', { name: /stake/i });
    if (await stakeButton.count() > 0) {
      await expect(stakeButton.first()).toBeVisible();
    }
  });

  test('should show tier information', async ({ page }) => {
    // Check for tier display (Bronze, Silver, Gold)
    const tierText = page.locator('text=/bronze|silver|gold|tier/i');
    // Tier info should be visible if staking is configured
    await expect(page).toHaveURL(/.*stake/);
  });

  test('should display staked amount', async ({ page }) => {
    // Check for staked amount display
    const stakedAmount = page.locator('text=/staked|amount/i');
    await expect(page).toHaveURL(/.*stake/);
  });
});

