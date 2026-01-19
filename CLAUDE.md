# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kids Rewards is a full-stack application for family chore and reward management. Parents can create chores, manage rewards, and kids can earn points by completing tasks. Includes a Pet Care Module for managing family pets and assigning care tasks.

## Architecture

### Backend (FastAPI + AWS Lambda)
- **main.py**: FastAPI application wrapped with Mangum for Lambda deployment
- **crud.py**: DynamoDB operations for all entities
- **models.py**: Pydantic models and data schemas
- **security.py**: JWT token handling and password hashing
- **Deployment**: Docker container on AWS Lambda via SAM template
- **Database**: DynamoDB with 11 tables

### Frontend (React + TypeScript)
- **App.tsx**: Main application with routing and context providers
- **services/api.ts**: Axios client with interceptors for authentication
- **UI Framework**: Mantine v8 components
- **Routing**: React Router v6
- **State**: React Context for authentication and user data

### Database Tables
| Table | Purpose |
|-------|---------|
| KidsRewardsUsers | User accounts and points |
| KidsRewardsStoreItems | Redeemable rewards |
| KidsRewardsPurchaseLogs | Purchase history |
| KidsRewardsChores | Chore definitions |
| KidsRewardsChoreLogs | Chore completion logs |
| KidsRewardsChoreAssignments | Assigned chores |
| KidsRewardsRequests | Kid requests for items/chores |
| KidsRewardsPets | Pet profiles |
| KidsRewardsPetCareSchedules | Recurring care schedules |
| KidsRewardsPetCareTasks | Task instances |
| KidsRewardsPetHealthLogs | Pet weight/health tracking |

## Essential Commands

### Quick Start (Recommended)
```bash
just dev          # Full environment with tmux (requires SAM + Docker)
just dev-simple   # Simpler setup - starts DynamoDB, gives terminal instructions
```

### Individual Services
```bash
just backend          # Start backend with SAM local (port 3000)
just backend-uvicorn  # Alternative: Start backend with uvicorn (no Docker needed)
just frontend         # Start frontend (port 3001)
just db-start-detached  # Start DynamoDB local
just db-create-tables   # Create all DynamoDB tables
```

### Testing
```bash
just test           # Run all tests (backend + frontend unit)
just test-backend   # Backend tests (pytest) - 61+ tests
just test-frontend  # Frontend unit tests (Jest) - 15+ tests
just e2e            # Playwright E2E tests - 22+ tests
just e2e-chrome     # E2E tests on Chrome only
```

### Code Quality
```bash
just format       # Format and lint all code
just lint-backend # Ruff check
just fix-backend  # Ruff fix and format
```

## Local Development Configuration

### Port Assignments
- **3000**: Backend API (SAM Local or uvicorn)
- **3001**: Frontend (React dev server)
- **8000**: DynamoDB Local

### Test Credentials
- Parent: `testparent` / `password456`
- Kid: `testkid` / `password123`

### Environment Variables
Backend requires these environment variables (set automatically by `just` commands):
- `DYNAMODB_ENDPOINT_OVERRIDE`: http://localhost:8000
- `APP_SECRET_KEY`: Any string for local dev
- Table names: `USERS_TABLE_NAME`, `PETS_TABLE_NAME`, etc.

## Key Implementation Details

### Authentication Flow
1. POST `/token` with username/password form data
2. Returns JWT token valid for 30 minutes
3. Frontend stores in localStorage and adds to Authorization header
4. Backend validates via `get_current_user` dependency

### Role-Based Access
- **Parent role**: Creating chores, managing store, approving purchases, managing pets
- **Kid role**: Completing chores, requesting purchases, viewing assigned tasks

### Frontend Patterns
- Mantine v8 components (TextInput, Select, Modal, etc.)
- Components don't use `name` attributes - use `placeholder` or `label` for selectors
- React Router v6 for routing
- Axios interceptors for auth tokens

### Testing Notes
- **Backend**: pytest with `APP_SECRET_KEY` environment variable
- **Frontend Unit**: React Testing Library with custom test-utils wrapper
- **E2E**: Playwright - use `placeholder` selectors for Mantine inputs
  ```typescript
  // Correct E2E selector for Mantine TextInput
  page.locator('input[placeholder="Your username"]')
  // NOT: page.locator('input[name="username"]')
  ```

## Pet Care Module

### Features
- **Manage Pets**: Add/edit pets with species, birthday, photo
- **Care Schedules**: Create recurring feeding/cleaning/exercise schedules
- **Task Instances**: Auto-generated daily tasks from schedules
- **Task Assignment**: Assign care tasks to kids for points
- **Health Tracking**: Log pet weight over time

### Pet Care Routes
| Route | Page | Access |
|-------|------|--------|
| /parent/manage-pets | ManagePetsPage | Parent |
| /parent/pet-schedules | ManageSchedulesPage | Parent |
| /parent/pending-pet-tasks | PendingPetTasksPage | Parent |
| /my-pet-tasks | MyPetTasksPage | Kid |
| /pet-care-overview | PetCareOverviewPage | All |
| /pet-health | PetHealthPage | All |

### API Endpoints
- `GET/POST /pets/` - List/create pets
- `GET/PUT/DELETE /pets/{id}` - Pet CRUD
- `GET/POST /pets/{pet_id}/schedules/` - Care schedules
- `GET /pets/tasks/my-tasks` - Kid's assigned tasks
- `POST /pets/tasks/{id}/submit` - Submit task completion
- `GET /pets/overview/` - Pet care dashboard data

## Troubleshooting

### SAM "Docker not found" Error
If `just backend` shows "Running AWS SAM projects locally requires Docker" even when Docker is running:
```bash
# Option 1: Restart Docker and try again
docker ps  # Verify Docker works
just backend

# Option 2: Use uvicorn instead (faster startup, no Docker needed)
just backend-uvicorn
```

### Login 500 Error
- Usually DynamoDB connection issue
- Ensure DynamoDB is running: `just db-start-detached`
- Check tables exist: `just db-list`

### Port Conflicts
```bash
lsof -i :3000  # Check what's using backend port
lsof -i :3001  # Check what's using frontend port
lsof -i :8000  # Check what's using DynamoDB port
```

### Container Issues
```bash
docker ps -a  # Check container status
docker start dynamodb-local  # Restart if stopped
docker rm dynamodb-local && just db-start-detached  # Recreate if broken
```

## Common Development Tasks

### Add New API Endpoint
1. Add route in main.py with appropriate dependencies
2. Implement CRUD operations in crud.py
3. Add models in models.py
4. Update frontend API client in services/api.ts
5. Add TypeScript interfaces for request/response

### Add New DynamoDB Table
1. Update backend/template.yaml with table definition
2. Add table name to environment variables in local-env.json
3. Add table creation to `just db-create-tables` in Justfile
4. Initialize table resource in crud.py
5. Add CRUD operations for new entity

### Run Single Test
```bash
# Backend
cd backend && pytest tests/test_specific.py::test_function_name -v

# Frontend
cd frontend && npm test -- --testNamePattern="test description"

# E2E single file
just e2e-file pet-care.spec.ts
```

## CI/CD Pipeline

### GitHub Actions
- Triggers on push/PR to main and feature branches
- Runs Ruff linting and formatting checks
- Executes pytest with coverage
- Tests frontend build

### Pre-commit Hook
```bash
just pre-commit  # Run checks manually
```

### Production Deployment
- AWS Lambda via SAM for backend
- AWS Amplify for frontend
- ECR for Docker images
- GitHub Actions for automated deployment on main branch
