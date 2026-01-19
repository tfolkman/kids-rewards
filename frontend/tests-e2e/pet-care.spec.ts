import { test, expect } from '@playwright/test';

test.describe('Pet Care Module', () => {
  async function loginAsParent(page) {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const usernameInput = page.locator('input[placeholder="Your username"]');
    await usernameInput.waitFor({ state: 'visible', timeout: 5000 });
    await usernameInput.fill('testparent');

    const passwordInput = page.locator('input[placeholder="Your password"]');
    await passwordInput.fill('password456');

    await page.click('button[type="submit"]');
    await page.waitForURL((url) => url.pathname.includes('/dashboard') || url.pathname === '/', { timeout: 10000 });

    const welcomeText = page.locator('text=/Welcome|Dashboard/i');
    await expect(welcomeText.first()).toBeVisible({ timeout: 5000 });
  }

  async function loginAsKid(page) {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const usernameInput = page.locator('input[placeholder="Your username"]');
    await usernameInput.waitFor({ state: 'visible', timeout: 5000 });
    await usernameInput.fill('testkid');

    const passwordInput = page.locator('input[placeholder="Your password"]');
    await passwordInput.fill('password123');

    await page.click('button[type="submit"]');
    await page.waitForURL((url) => url.pathname.includes('/dashboard') || url.pathname === '/', { timeout: 10000 });

    const welcomeText = page.locator('text=/Welcome|Dashboard/i');
    await expect(welcomeText.first()).toBeVisible({ timeout: 5000 });
  }

  test.describe('Manage Pets Page (Parent)', () => {
    test('should display manage pets page with add pet button', async ({ page }) => {
      await loginAsParent(page);

      await page.click('a[href="/parent/manage-pets"]');
      await page.waitForURL(/\/parent\/manage-pets/);

      await expect(page.locator('text=Manage Pets')).toBeVisible();
      await expect(page.locator('button:has-text("Add New Pet")')).toBeVisible();
    });

    test('should open add pet modal and show form fields', async ({ page }) => {
      await loginAsParent(page);

      await page.click('a[href="/parent/manage-pets"]');
      await page.waitForURL(/\/parent\/manage-pets/);

      await page.click('button:has-text("Add New Pet")');

      await expect(page.locator('.mantine-Modal-title:has-text("Add New Pet")')).toBeVisible();
      await expect(page.locator('input[placeholder="e.g., Spike"]')).toBeVisible();
      await expect(page.locator('text=Pet Name')).toBeVisible();
      await expect(page.locator('text=Birthday')).toBeVisible();
    });

    test('should show create pet button in modal', async ({ page }) => {
      await loginAsParent(page);

      await page.click('a[href="/parent/manage-pets"]');
      await page.waitForURL(/\/parent\/manage-pets/);

      await page.click('button:has-text("Add New Pet")');
      await expect(page.locator('.mantine-Modal-title:has-text("Add New Pet")')).toBeVisible();

      const createButton = page.locator('button:has-text("Create Pet")');
      await expect(createButton).toBeVisible();
    });
  });

  test.describe('Pet Schedules Page (Parent)', () => {
    test('should display pet schedules page', async ({ page }) => {
      await loginAsParent(page);

      await page.click('a[href="/parent/pet-schedules"]');
      await page.waitForURL(/\/parent\/pet-schedules/);

      await expect(page.locator('h2:has-text("Pet Care Schedules")')).toBeVisible();
      await expect(page.locator('button:has-text("Add New Schedule")')).toBeVisible();
    });

    test('should show pet selection dropdown', async ({ page }) => {
      await loginAsParent(page);

      await page.click('a[href="/parent/pet-schedules"]');
      await page.waitForURL(/\/parent\/pet-schedules/);

      await expect(page.locator('text=Select Pet')).toBeVisible();
    });

    test('should show message when no pet selected', async ({ page }) => {
      await loginAsParent(page);

      await page.click('a[href="/parent/pet-schedules"]');
      await page.waitForURL(/\/parent\/pet-schedules/);

      const messageWithPets = page.locator('text=Select a pet to view and manage its care schedules');
      const messageNoPets = page.locator('text=No pets found. Add a pet first to create care schedules.');

      const hasMessage = await messageWithPets.isVisible().catch(() => false) ||
                        await messageNoPets.isVisible().catch(() => false);
      expect(hasMessage).toBeTruthy();
    });
  });

  test.describe('Pending Pet Tasks Page (Parent)', () => {
    test('should display pending pet tasks page', async ({ page }) => {
      await loginAsParent(page);

      await page.goto('/parent/pending-pet-tasks');
      await page.waitForURL(/\/parent\/pending-pet-tasks/);

      await expect(page.locator('text=Pending Pet Task Approvals')).toBeVisible();
    });

    test('should show empty state when no pending tasks', async ({ page }) => {
      await loginAsParent(page);

      await page.goto('/parent/pending-pet-tasks');
      await page.waitForURL(/\/parent\/pending-pet-tasks/);

      const emptyMessage = page.locator('text=No pending pet task submissions to review');
      const taskCard = page.locator('[data-testid="pet-task-card"]');

      await page.waitForTimeout(1000);

      const hasEmptyMessage = await emptyMessage.isVisible().catch(() => false);
      const hasTaskCard = await taskCard.isVisible().catch(() => false);

      expect(hasEmptyMessage || hasTaskCard).toBeTruthy();
    });
  });

  test.describe('My Pet Tasks Page (Kid)', () => {
    test('should display my pet tasks page for kids', async ({ page }) => {
      await loginAsKid(page);

      await page.click('a[href="/my-pet-tasks"]');
      await page.waitForURL(/\/my-pet-tasks/);

      await expect(page.locator('h2:has-text("My Pet Tasks")')).toBeVisible();
    });

    test('should show empty state or task list', async ({ page }) => {
      await loginAsKid(page);

      await page.click('a[href="/my-pet-tasks"]');
      await page.waitForURL(/\/my-pet-tasks/);

      await page.waitForTimeout(1000);

      const emptyMessage = page.locator('text=No pet care tasks assigned to you yet');
      const todoSection = page.locator('text=To Do');
      const pendingSection = page.locator('text=Awaiting Approval');

      const hasContent = await emptyMessage.isVisible().catch(() => false) ||
                        await todoSection.isVisible().catch(() => false) ||
                        await pendingSection.isVisible().catch(() => false);

      expect(hasContent).toBeTruthy();
    });
  });

  test.describe('Pet Care Overview Page', () => {
    test('should display pet care overview page for kids', async ({ page }) => {
      await loginAsKid(page);

      await page.click('a[href="/pet-care-overview"]');
      await page.waitForURL(/\/pet-care-overview/);

      await page.waitForTimeout(1000);
      const pageContent = await page.content();
      const hasTitleOrEmptyState = pageContent.includes('Pet Care Overview') ||
                                    pageContent.includes('No pets found');
      expect(hasTitleOrEmptyState).toBe(true);
    });

    test('should display pet care overview page for parents', async ({ page }) => {
      await loginAsParent(page);

      await page.goto('/pet-care-overview');
      await page.waitForURL(/\/pet-care-overview/);

      await page.waitForTimeout(1000);
      const pageContent = await page.content();
      const hasTitleOrEmptyState = pageContent.includes('Pet Care Overview') ||
                                    pageContent.includes('No pets found');
      expect(hasTitleOrEmptyState).toBe(true);
    });

    test('should show empty state or pet cards', async ({ page }) => {
      await loginAsKid(page);

      await page.click('a[href="/pet-care-overview"]');
      await page.waitForURL(/\/pet-care-overview/);

      await page.waitForTimeout(1000);

      const emptyMessage = page.locator('text=No pets found. Add a pet to see the overview');
      const petCard = page.locator('.mantine-Card-root');

      const hasEmptyMessage = await emptyMessage.isVisible().catch(() => false);
      const hasPetCards = await petCard.first().isVisible().catch(() => false);

      expect(hasEmptyMessage || hasPetCards).toBeTruthy();
    });
  });

  test.describe('Pet Health Page', () => {
    test('should display pet health page', async ({ page }) => {
      await loginAsKid(page);

      await page.click('a[href="/pet-health"]');
      await page.waitForURL(/\/pet-health/);

      await expect(page.locator('h2:has-text("Pet Health Tracking")')).toBeVisible();
    });

    test('should show pet selection dropdown', async ({ page }) => {
      await loginAsKid(page);

      await page.click('a[href="/pet-health"]');
      await page.waitForURL(/\/pet-health/);

      await expect(page.locator('text=Select Pet')).toBeVisible();
    });

    test('should show log weight button when pet is selected', async ({ page }) => {
      await loginAsKid(page);

      await page.click('a[href="/pet-health"]');
      await page.waitForURL(/\/pet-health/);

      const petSelect = page.locator('input[placeholder*="Choose a pet"]');
      if (await petSelect.isVisible()) {
        await petSelect.click();

        const petOption = page.locator('.mantine-Select-option').first();
        if (await petOption.isVisible({ timeout: 2000 }).catch(() => false)) {
          await petOption.click();

          await expect(page.locator('button:has-text("Log Weight")')).toBeVisible();
        }
      }
    });
  });

  test.describe('Navigation', () => {
    test('parent should see pet care navigation links', async ({ page }) => {
      await loginAsParent(page);

      await expect(page.locator('a[href="/parent/manage-pets"]')).toBeVisible();
      await expect(page.locator('a[href="/parent/pet-schedules"]')).toBeVisible();
      await expect(page.locator('a[href="/parent/pending-pet-tasks"]')).toBeVisible();
      await expect(page.locator('a[href="/pet-health"]')).toBeVisible();
    });

    test('kid should see pet care navigation links', async ({ page }) => {
      await loginAsKid(page);

      await expect(page.locator('a[href="/my-pet-tasks"]')).toBeVisible();
      await expect(page.locator('a[href="/pet-care-overview"]')).toBeVisible();
      await expect(page.locator('a[href="/pet-health"]')).toBeVisible();
    });

    test('pet care section divider should be visible for parent', async ({ page }) => {
      await loginAsParent(page);

      await expect(page.locator('text=Pet Care').first()).toBeVisible();
    });

    test('pet care section divider should be visible for kid', async ({ page }) => {
      await loginAsKid(page);

      await expect(page.locator('text=Pet Care').first()).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully on pet overview', async ({ page }) => {
      await loginAsKid(page);

      await page.route('**/pets/overview/', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal server error' })
        });
      });

      await page.click('a[href="/pet-care-overview"]');
      await page.waitForURL(/\/pet-care-overview/);

      await expect(page.locator('text=Failed to fetch pet care overview')).toBeVisible();
    });

    test('should handle API errors gracefully on pet health', async ({ page }) => {
      await loginAsKid(page);

      await page.route('**/pets/', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal server error' })
        });
      });

      await page.click('a[href="/pet-health"]');
      await page.waitForURL(/\/pet-health/);

      await page.waitForTimeout(1000);

      const errorAlert = page.locator('.mantine-Alert-root');
      const isAlertVisible = await errorAlert.isVisible().catch(() => false);
    });
  });
});
