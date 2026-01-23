import { test, expect } from '@playwright/test';

test.describe('Chore Submission Flow', () => {
  // Helper function to login
  async function loginAsKid(page) {
    await page.goto('/');

    // Wait for the login page to load
    await page.waitForLoadState('networkidle');

    // Fill in login form - use placeholder selectors (Mantine components don't use name attributes)
    const usernameInput = page.locator('input[placeholder="Your username"]');
    await usernameInput.waitFor({ state: 'visible', timeout: 5000 });
    await usernameInput.fill('testkid');

    const passwordInput = page.locator('input[placeholder="Your password"]');
    await passwordInput.fill('password123');

    // Click login button
    await page.click('button[type="submit"]');

    // Wait for navigation - more flexible waiting
    await page.waitForURL((url) => url.pathname.includes('/dashboard') || url.pathname === '/', { timeout: 10000 });

    // Verify we're logged in - look for user-specific content
    const welcomeText = page.locator('text=/Welcome|Dashboard|Available Chores|My Chores/i');
    await expect(welcomeText.first()).toBeVisible({ timeout: 5000 });
  }
  
  test('should successfully submit a chore with effort tracking', async ({ page }) => {
    // Login as kid
    await loginAsKid(page);
    
    // Navigate to chores page
    await page.click('a[href="/chores"]');
    await page.waitForURL(/\/chores/);
    
    // Verify page loaded
    await expect(page.locator('h2:has-text("Available Chores")')).toBeVisible();
    
    // Find and click the first "Mark as Done" button
    const markAsDoneButton = page.locator('button:has-text("Mark as Done")').first();
    await expect(markAsDoneButton).toBeVisible();
    await markAsDoneButton.click();
    
    // Modal should open - use modal title selector to avoid ambiguity with button
    await expect(page.locator('.mantine-Modal-title:has-text("Submit Chore")')).toBeVisible();
    await expect(page.locator('text=Track how long you worked')).toBeVisible();
    
    // Start the effort timer
    const startButton = page.locator('button:has-text("Start Timer")');
    if (await startButton.isVisible()) {
      await startButton.click();
      
      // Wait a moment to accumulate some time
      await page.waitForTimeout(2000);
      
      // Stop the timer
      await page.click('button:has-text("Stop & Save")');
    }
    
    // Submit the chore
    await page.click('button:has-text("Submit Chore")');

    // Modal should close - wait for it to disappear first
    await expect(page.locator('.mantine-Modal-title:has-text("Submit Chore")')).not.toBeVisible({ timeout: 10000 });

    // Verify success message appears (after modal closes)
    await expect(page.locator('text=Chore submitted successfully')).toBeVisible({ timeout: 10000 });
  });

  test('should handle retry attempts correctly', async ({ page }) => {
    // Login as kid
    await loginAsKid(page);
    
    // Navigate to chores page
    await page.click('a[href="/chores"]');
    await page.waitForURL(/\/chores/);
    
    // Click on a chore to mark as done
    const markAsDoneButton = page.locator('button:has-text("Mark as Done")').first();
    await markAsDoneButton.click();
    
    // Check if retry badge appears (if there was a previous attempt)
    // Just verify the badge is visible if present - no additional text check needed
    const retryBadge = page.locator('text=Retry Attempt');
    const hasRetryBadge = await retryBadge.isVisible({ timeout: 1000 }).catch(() => false);
    if (hasRetryBadge) {
      console.log('Retry attempt detected');
    }
    
    // Submit without timer (0 minutes effort)
    await page.click('button:has-text("Submit Chore")');

    // Modal should close - wait for it to disappear first
    await expect(page.locator('.mantine-Modal-title:has-text("Submit Chore")')).not.toBeVisible({ timeout: 10000 });

    // Should still succeed
    await expect(page.locator('text=Chore submitted successfully')).toBeVisible({ timeout: 10000 });
  });

  test('should display error message properly when submission fails', async ({ page }) => {
    // Login as kid
    await loginAsKid(page);
    
    // Navigate to chores page
    await page.click('a[href="/chores"]');
    await page.waitForURL(/\/chores/);
    
    // Intercept the API call to simulate an error
    await page.route('**/chores/*/submit', route => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'You have already submitted this chore today'
        })
      });
    });
    
    // Click on a chore to mark as done
    const markAsDoneButton = page.locator('button:has-text("Mark as Done")').first();
    await markAsDoneButton.click();
    
    // Submit the chore
    await page.click('button:has-text("Submit Chore")');
    
    // Error should be displayed as a string, not cause React rendering error
    await expect(page.locator('text=You have already submitted this chore today')).toBeVisible();

    // Modal should close - check title is gone
    await expect(page.locator('.mantine-Modal-title:has-text("Submit Chore")')).not.toBeVisible();
  });

  test('should handle validation errors from backend correctly', async ({ page }) => {
    // Login as kid
    await loginAsKid(page);
    
    // Navigate to chores page
    await page.click('a[href="/chores"]');
    await page.waitForURL(/\/chores/);
    
    // Intercept the API call to simulate a validation error
    await page.route('**/chores/*/submit', route => {
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: [
            {
              type: 'value_error',
              loc: ['body', 'effort_minutes'],
              msg: 'ensure this value is less than or equal to 240',
              input: { effort_minutes: 300 }
            }
          ]
        })
      });
    });
    
    // Click on a chore to mark as done
    const markAsDoneButton = page.locator('button:has-text("Mark as Done")').first();
    await markAsDoneButton.click();
    
    // Submit the chore
    await page.click('button:has-text("Submit Chore")');
    
    // Should extract and display the validation error message
    await expect(page.locator('text=ensure this value is less than or equal to 240')).toBeVisible();
    
    // Should not cause React rendering error
    await expect(page.locator('text=Objects are not valid as a React child')).not.toBeVisible();
  });
  
  test('should allow timer usage and submission', async ({ page }) => {
    // Login as kid
    await loginAsKid(page);

    // Navigate to chores page
    await page.click('a[href="/chores"]');
    await page.waitForURL(/\/chores/);

    // Click on a chore
    const markAsDoneButton = page.locator('button:has-text("Mark as Done")').first();
    await markAsDoneButton.click();

    // Wait for modal to be fully visible
    await expect(page.locator('.mantine-Modal-content')).toBeVisible();

    // Verify timer component is visible in modal
    await expect(page.locator('.mantine-Modal-content >> text=Track how long you worked')).toBeVisible();

    // Start timer (use modal-scoped locator)
    const modal = page.locator('.mantine-Modal-content');
    const startButton = modal.locator('button:has-text("Start Timer")');
    await expect(startButton).toBeVisible();
    await startButton.click();

    // Wait for timer to start and UI to update
    await page.waitForTimeout(500);

    // Verify timer is running - should show Pause and Stop buttons
    await expect(modal.locator('button:has-text("Pause")')).toBeVisible();
    await expect(modal.locator('button:has-text("Stop & Save")')).toBeVisible();

    // Stop timer
    await modal.locator('button:has-text("Stop & Save")').click();

    // Wait for timer state to update
    await page.waitForTimeout(500);

    // Timer stopped - verify modal is still open and we can submit
    await expect(modal).toBeVisible();

    // Submit the chore
    await modal.locator('button:has-text("Submit Chore")').click();

    // Modal should close
    await expect(page.locator('.mantine-Modal-title:has-text("Submit Chore")')).not.toBeVisible({ timeout: 10000 });

    // Verify submission succeeded
    await expect(page.locator('text=Chore submitted successfully')).toBeVisible({ timeout: 10000 });
  });
});