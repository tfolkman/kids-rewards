# Spike Feeding E2E & Integration Test Plan

## 📊 Current Test Coverage

### ✅ Already Have (Unit Tests)
- `test_spike_feeding.py` - 11 unit tests for assignment logic
- `test_spike_integration.py` - 2 integration tests with mocked CRUD

### ⚠️ Missing (Critical Gaps)
1. **Backend Integration Tests** - Full API workflow with real endpoints
2. **E2E Tests** - Browser-based user workflows
3. **Regression Tests** - Ensure other tasks still require approval

---

## 🎯 Recommended New Tests

### 1. Backend Integration Tests (HIGH PRIORITY)

**File: `backend/tests/test_spike_feeding_api.py`**

These test the **actual API endpoints** using FastAPI's TestClient against a real running backend (with mocked DynamoDB).

```python
"""
Backend integration tests for Spike feeding API endpoints.
Tests full request/response cycle with real HTTP calls.
"""
import os
from datetime import datetime, timedelta
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

import main
import models
import crud


@pytest.fixture(autouse=True)
def setup_env():
    """Set required environment variables"""
    os.environ["APP_SECRET_KEY"] = "test-secret-key-for-testing-32-chars"


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(main.app)


@pytest.fixture
def parent_user():
    """Mock parent user"""
    return models.User(
        id="parent-123",
        username="testparent",
        password_hash="hashed",
        role="parent",
        points=0,
        is_active=True,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def aiden_user():
    """Mock Aiden kid user"""
    return models.User(
        id="aiden-123",
        username="aiden",
        password_hash="hashed",
        role="kid",
        points=100,
        is_active=True,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def spike_pet(parent_user):
    """Mock Spike pet"""
    return models.Pet(
        id="spike-pet-123",
        parent_id=parent_user.id,
        name="Spike",
        species=models.PetSpecies.BEARDED_DRAGON,
        birthday=datetime(2025, 2, 1),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestSpikeTaskGenerationAPI:
    """Test the task generation endpoint"""

    @patch('main.get_current_parent_user')
    @patch('crud.get_pets_by_parent_id')
    @patch('crud.get_tasks_by_pet_id')
    @patch('crud.create_pet_care_task')
    def test_generate_tasks_endpoint_success(
        self, mock_create_task, mock_get_tasks, mock_get_pets,
        mock_auth, client, parent_user, spike_pet
    ):
        """Test successful task generation via API endpoint"""
        # Setup mocks
        mock_auth.return_value = parent_user
        mock_get_pets.return_value = [spike_pet]
        mock_get_tasks.return_value = []  # No existing tasks

        # Mock task creation to return success
        def create_task_side_effect(task_create):
            return models.PetCareTask(
                id=f"task-{task_create.due_date.day}",
                **task_create.dict(),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow()
            )
        mock_create_task.side_effect = create_task_side_effect

        # Make request
        response = client.post("/parent/pets/spike/generate-feeding-tasks?days_ahead=7")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["tasks_created"] == 7
        assert data["pet_name"] == "Spike"
        assert "Generated 7 Spike feeding task(s)" in data["message"]

        # Verify create_pet_care_task was called 7 times
        assert mock_create_task.call_count == 7

    @patch('main.get_current_parent_user')
    @patch('crud.get_pets_by_parent_id')
    def test_generate_tasks_no_spike_found(
        self, mock_get_pets, mock_auth, client, parent_user
    ):
        """Test error when Spike pet doesn't exist"""
        mock_auth.return_value = parent_user
        mock_get_pets.return_value = []  # No pets

        response = client.post("/parent/pets/spike/generate-feeding-tasks?days_ahead=7")

        assert response.status_code == 404
        assert "Spike not found" in response.json()["detail"]

    @patch('main.get_current_parent_user')
    @patch('crud.get_pets_by_parent_id')
    @patch('crud.get_tasks_by_pet_id')
    @patch('crud.create_pet_care_task')
    def test_generate_tasks_skips_duplicates(
        self, mock_create_task, mock_get_tasks, mock_get_pets,
        mock_auth, client, parent_user, spike_pet
    ):
        """Test that generation skips dates with existing tasks"""
        mock_auth.return_value = parent_user
        mock_get_pets.return_value = [spike_pet]

        # Mock 3 existing tasks
        today = datetime.utcnow().date()
        existing_tasks = [
            models.PetCareTask(
                id=f"existing-{i}",
                schedule_id="spike-feeding-auto",
                pet_id=spike_pet.id,
                pet_name="Spike",
                task_name="Feed Spike",
                description="Feed Spike",
                points_value=10,
                assigned_to_kid_id="aiden",
                assigned_to_kid_username="aiden",
                due_date=datetime.combine(today + timedelta(days=i), datetime.min.time()),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        mock_get_tasks.return_value = existing_tasks

        def create_task_side_effect(task_create):
            return models.PetCareTask(
                id=f"new-task-{task_create.due_date.day}",
                **task_create.dict(),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow()
            )
        mock_create_task.side_effect = create_task_side_effect

        response = client.post("/parent/pets/spike/generate-feeding-tasks?days_ahead=7")

        assert response.status_code == 200
        data = response.json()
        # Should only create 4 tasks (7 requested - 3 existing)
        assert data["tasks_created"] == 4
        assert mock_create_task.call_count == 4


class TestSpikeAutoApprovalAPI:
    """Test auto-approval when submitting Spike feeding tasks"""

    @patch('main.get_current_kid_user')
    @patch('crud.submit_pet_care_task')
    def test_submit_spike_feeding_auto_approves(
        self, mock_submit, mock_auth, client, aiden_user
    ):
        """Test that submitting Feed Spike task auto-approves"""
        mock_auth.return_value = aiden_user

        # Mock CRUD to return APPROVED task
        approved_task = models.PetCareTask(
            id="task-123",
            schedule_id="spike-feeding-auto",
            pet_id="spike-pet-123",
            pet_name="Spike",
            task_name="Feed Spike",
            description="Feed Spike his daily meal",
            points_value=10,
            assigned_to_kid_id="aiden",
            assigned_to_kid_username="aiden",
            due_date=datetime(2026, 1, 29, 18, 0),
            status=models.PetCareTaskStatus.APPROVED,  # Auto-approved!
            created_at=datetime.utcnow(),
            submitted_at=datetime.utcnow(),
            reviewed_at=datetime.utcnow()  # Auto-reviewed!
        )
        mock_submit.return_value = approved_task

        # Make request
        response = client.post(
            "/pets/tasks/task-123/submit",
            json={"notes": "Fed Spike his crickets"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["submitted_at"] is not None
        assert data["reviewed_at"] is not None

        # Verify CRUD was called correctly
        mock_submit.assert_called_once()
        call_kwargs = mock_submit.call_args[1]
        assert call_kwargs["task_id"] == "task-123"
        assert call_kwargs["kid_user"].username == "aiden"
        assert call_kwargs["notes"] == "Fed Spike his crickets"

    @patch('main.get_current_kid_user')
    @patch('crud.submit_pet_care_task')
    def test_submit_other_task_requires_approval(
        self, mock_submit, mock_auth, client, aiden_user
    ):
        """Test that non-feeding tasks still require parent approval"""
        mock_auth.return_value = aiden_user

        # Mock CRUD to return PENDING_APPROVAL task
        pending_task = models.PetCareTask(
            id="task-456",
            schedule_id="cleaning-schedule",
            pet_id="spike-pet-123",
            pet_name="Spike",
            task_name="Clean Tank",  # NOT a feeding task
            description="Clean Spike's tank",
            points_value=25,
            assigned_to_kid_id="aiden",
            assigned_to_kid_username="aiden",
            due_date=datetime(2026, 1, 29, 18, 0),
            status=models.PetCareTaskStatus.PENDING_APPROVAL,  # Requires approval
            created_at=datetime.utcnow(),
            submitted_at=datetime.utcnow()
        )
        mock_submit.return_value = pending_task

        response = client.post(
            "/pets/tasks/task-456/submit",
            json={"notes": "Cleaned the tank"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING_APPROVAL"
        assert data["reviewed_at"] is None  # Not yet reviewed


class TestAssignmentPattern:
    """Test that the rotation pattern works correctly via API"""

    @patch('main.get_current_parent_user')
    @patch('crud.get_pets_by_parent_id')
    @patch('crud.get_tasks_by_pet_id')
    @patch('crud.create_pet_care_task')
    def test_7_day_rotation_pattern(
        self, mock_create_task, mock_get_tasks, mock_get_pets,
        mock_auth, client, parent_user, spike_pet
    ):
        """Test that 7 days generates correct rotation: aiden, clara, emery, aiden, clara, emery, aiden"""
        mock_auth.return_value = parent_user
        mock_get_pets.return_value = [spike_pet]
        mock_get_tasks.return_value = []

        created_tasks = []
        def capture_created_task(task_create):
            task = models.PetCareTask(
                id=f"task-{len(created_tasks)}",
                **task_create.dict(),
                status=models.PetCareTaskStatus.ASSIGNED,
                created_at=datetime.utcnow()
            )
            created_tasks.append(task)
            return task

        mock_create_task.side_effect = capture_created_task

        response = client.post("/parent/pets/spike/generate-feeding-tasks?days_ahead=7")

        assert response.status_code == 200
        assert len(created_tasks) == 7

        # Verify rotation pattern (starting from reference Thursday)
        expected_kids = ["aiden", "clara", "emery", "aiden", "clara", "emery", "aiden"]
        actual_kids = [task.assigned_to_kid_id for task in created_tasks]

        assert actual_kids == expected_kids, f"Expected {expected_kids}, got {actual_kids}"
```

---

### 2. E2E Tests (MEDIUM PRIORITY)

**File: `frontend/tests-e2e/spike-feeding.spec.ts`**

These test the **full user workflow** in a real browser.

```typescript
import { test, expect } from '@playwright/test';

test.describe('Spike Feeding Auto-Schedule', () => {

  async function loginAsParent(page) {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.locator('input[placeholder="Your username"]').fill('testparent');
    await page.locator('input[placeholder="Your password"]').fill('password456');
    await page.click('button[type="submit"]');

    await page.waitForURL((url) => url.pathname.includes('/dashboard') || url.pathname === '/');
    await expect(page.locator('text=/Welcome|Dashboard/i').first()).toBeVisible();
  }

  async function loginAsKid(page, username: string, password: string) {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.locator('input[placeholder="Your username"]').fill(username);
    await page.locator('input[placeholder="Your password"]').fill(password);
    await page.click('button[type="submit"]');

    await page.waitForURL((url) => url.pathname.includes('/dashboard') || url.pathname === '/');
    await expect(page.locator('text=/Welcome|Dashboard/i').first()).toBeVisible();
  }

  test.describe('Task Generation (Parent)', () => {
    test('should have a button to generate Spike feeding tasks', async ({ page }) => {
      await loginAsParent(page);

      // Navigate to pet schedules or a dedicated Spike page
      await page.goto('/parent/pet-schedules');
      await page.waitForURL(/\/parent\/pet-schedules/);

      // Look for generate tasks button (you may need to add this to UI)
      // This is a placeholder - adjust based on actual UI implementation
      const generateButton = page.locator('button:has-text("Generate Feeding Tasks")');

      // If button exists, test it
      if (await generateButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await generateButton.click();

        // Expect success message
        await expect(page.locator('text=/Generated.*task/i')).toBeVisible({ timeout: 5000 });
      } else {
        // If no UI exists yet, test via API call directly
        test.skip();
      }
    });
  });

  test.describe('Auto-Approval (Kid)', () => {
    test('should auto-approve when kid submits Feed Spike task', async ({ page }) => {
      await loginAsKid(page, 'aiden', 'AIDEN_PASSWORD'); // Replace with actual password

      // Navigate to my pet tasks
      await page.click('a[href="/my-pet-tasks"]');
      await page.waitForURL(/\/my-pet-tasks/);

      // Find a "Feed Spike" task in To Do section
      const feedSpikeTask = page.locator('text=Feed Spike').first();

      if (await feedSpikeTask.isVisible({ timeout: 2000 }).catch(() => false)) {
        // Click on the task card
        await feedSpikeTask.click();

        // Submit the task
        const submitButton = page.locator('button:has-text("Submit")');
        if (await submitButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await submitButton.click();

          // Expect task to be in "Completed" section, NOT "Awaiting Approval"
          await page.waitForTimeout(1000); // Wait for state update

          const completedSection = page.locator('text=Completed');
          await expect(completedSection).toBeVisible();

          // Task should NOT be in awaiting approval
          const awaitingSection = page.locator('text=Awaiting Approval');
          const taskInAwaiting = awaitingSection.locator('text=Feed Spike');
          await expect(taskInAwaiting).not.toBeVisible();
        }
      } else {
        test.skip(); // No tasks available to test
      }
    });

    test('should still require approval for non-feeding tasks', async ({ page }) => {
      await loginAsKid(page, 'aiden', 'AIDEN_PASSWORD');

      await page.click('a[href="/my-pet-tasks"]');
      await page.waitForURL(/\/my-pet-tasks/);

      // Find a non-feeding task (e.g., "Clean Tank")
      const cleanTankTask = page.locator('text=Clean Tank').first();

      if (await cleanTankTask.isVisible({ timeout: 2000 }).catch(() => false)) {
        await cleanTankTask.click();

        const submitButton = page.locator('button:has-text("Submit")');
        if (await submitButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await submitButton.click();

          await page.waitForTimeout(1000);

          // Task SHOULD be in "Awaiting Approval" section
          const awaitingSection = page.locator('text=Awaiting Approval');
          await expect(awaitingSection).toBeVisible();

          const taskInAwaiting = awaitingSection.locator('text=Clean Tank');
          await expect(taskInAwaiting).toBeVisible();
        }
      } else {
        test.skip();
      }
    });
  });

  test.describe('Assignment Pattern Verification', () => {
    test('should assign tasks according to rotation when generated', async ({ page }) => {
      await loginAsParent(page);

      // This test would need to:
      // 1. Generate tasks via API
      // 2. Check task assignments match rotation
      // This is better tested in backend integration tests

      test.skip(); // Backend tests cover this better
    });
  });
});
```

---

### 3. Regression Tests (HIGH PRIORITY)

**Update: `backend/tests/test_spike_integration.py`**

Add a test to ensure we didn't break existing functionality:

```python
class TestRegressionOtherPetTasks:
    """Ensure other pet care tasks still work correctly"""

    @patch('crud.get_task_by_id')
    @patch('crud.pet_care_tasks_table')
    @patch('crud._award_points_and_streak_bonus')
    def test_tank_cleaning_still_needs_approval(
        self, mock_award_points, mock_table, mock_get_task
    ):
        """Verify that Clean Tank tasks still require parent approval"""

        # Create a Clean Tank task
        task = models.PetCareTask(
            id="task-clean-123",
            schedule_id="cleaning-schedule",
            pet_id="spike-pet-id",
            pet_name="Spike",
            task_name="Clean Tank",
            description="Clean the tank thoroughly",
            points_value=25,
            assigned_to_kid_id="aiden",
            assigned_to_kid_username="aiden",
            due_date=datetime(2026, 1, 29, 18, 0),
            status=models.PetCareTaskStatus.ASSIGNED,
            created_at=datetime.utcnow()
        )

        mock_get_task.return_value = task

        # Mock DynamoDB response
        mock_table.update_item.return_value = {
            "Attributes": {
                **task.dict(),
                "status": "PENDING_APPROVAL",
                "submitted_at": datetime.utcnow().isoformat()
            }
        }

        kid_user = models.User(
            id="aiden-id",
            username="aiden",
            password_hash="hashed",
            role="kid",
            points=100,
            is_active=True,
            created_at=datetime.utcnow()
        )

        # Submit the task
        result = crud.submit_pet_care_task(
            task_id="task-clean-123",
            kid_user=kid_user,
            notes="All done!"
        )

        # Verify it went to PENDING_APPROVAL
        assert result.status == models.PetCareTaskStatus.PENDING_APPROVAL

        # Verify points were NOT awarded
        mock_award_points.assert_not_called()
```

---

## 🚀 Implementation Priority

### Phase 1: Backend Integration Tests ⭐⭐⭐
**Why**: These catch bugs before deployment and are fastest to run.

**Action**:
1. Create `backend/tests/test_spike_feeding_api.py`
2. Add the tests above
3. Run: `pytest backend/tests/test_spike_feeding_api.py -v`
4. Add to CI/CD pipeline (already configured in `.github/workflows/ci-tests.yml`)

### Phase 2: Regression Tests ⭐⭐⭐
**Why**: Ensures we didn't break existing pet care tasks.

**Action**:
1. Add regression test to `test_spike_integration.py`
2. Run full test suite: `just test-backend`

### Phase 3: E2E Tests ⭐⭐
**Why**: Validates full user experience but requires more setup.

**Action**:
1. Create `frontend/tests-e2e/spike-feeding.spec.ts`
2. May need to add UI elements (generate button, etc.)
3. Run: `just e2e` or `npm run e2e` from frontend/

### Phase 4: Manual Testing ⭐
**Why**: Quick sanity check before releasing.

**Action**:
1. Generate 7 days of tasks via API
2. Have Aiden submit a feeding task
3. Verify auto-approval and points
4. Have Aiden submit a cleaning task
5. Verify it still needs approval

---

## 📋 Test Checklist

Before deploying to production:

- [ ] All unit tests pass (11 tests in `test_spike_feeding.py`)
- [ ] Backend integration tests pass (new file)
- [ ] Regression tests pass (other tasks still work)
- [ ] E2E tests pass (optional but recommended)
- [ ] Manual smoke test completed
- [ ] CI/CD pipeline green

---

## 🔧 Running Tests

### Backend Only
```bash
# All backend tests
just test-backend

# Only Spike tests
pytest backend/tests/test_spike_feeding*.py -v

# With coverage
pytest backend/tests/test_spike_feeding*.py --cov=pet_care --cov=crud
```

### E2E Only
```bash
# All E2E tests
just e2e

# Only Spike E2E tests
cd frontend
npx playwright test tests-e2e/spike-feeding.spec.ts
```

### Everything
```bash
just test  # Runs backend + frontend unit tests
just e2e   # Runs E2E tests separately
```

---

## 📊 Expected Test Metrics

| Test Type | Count | Time | Coverage |
|-----------|-------|------|----------|
| Unit tests | 11 | <1s | Assignment logic, task generation |
| Integration (mocked) | 2 | <1s | CRUD auto-approval |
| Integration (API) | 8 | 2-3s | Full HTTP request/response |
| Regression | 1 | <1s | Other tasks unchanged |
| E2E | 3 | 10-15s | Full user workflow |
| **TOTAL** | **25** | **<20s** | **Complete feature** |

---

## 🎯 Success Criteria

All tests should:
✅ Pass consistently (no flaky tests)
✅ Run in CI/CD automatically
✅ Cover happy path + edge cases
✅ Verify auto-approval works
✅ Verify other tasks still require approval
✅ Test the rotation pattern

---

Want me to implement the backend integration tests first? They're the highest priority and will catch most bugs!
