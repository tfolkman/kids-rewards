# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kids Rewards is a full-stack application for family chore and reward management. Parents can create chores, manage rewards, and kids can earn points by completing tasks.

## Architecture

### Backend (FastAPI + AWS Lambda)
- **main.py**: FastAPI application wrapped with Mangum for Lambda deployment
- **crud.py**: DynamoDB operations for all entities (users, chores, store items, etc.)
- **models.py**: Pydantic models and data schemas
- **security.py**: JWT token handling and password hashing
- **Deployment**: Docker container on AWS Lambda via SAM template
- **Database**: DynamoDB with 6 tables (Users, StoreItems, PurchaseLogs, Chores, ChoreLogs, Requests)

### Frontend (React + TypeScript)
- **App.tsx**: Main application with routing and context providers
- **services/api.ts**: Axios client with interceptors for authentication
- **UI Framework**: Mantine v8 components
- **Routing**: React Router v6
- **State**: React Context for authentication and user data

## Essential Commands

### Quick Start
```bash
just dev          # Start complete dev environment (recommended)
just stop         # Stop all services
```

### Individual Services
```bash
just backend      # Start backend API on port 3000
just frontend     # Start frontend on port 3001 (PORT=3001 is required)
just db-start-detached  # Start DynamoDB local
just db-create-tables   # Create all DynamoDB tables
```

### Testing
```bash
just test         # Run all tests
just test-backend # Backend tests (pytest)
just test-frontend # Frontend tests (React Testing Library)
just e2e          # Playwright E2E tests
```

### Code Quality
```bash
just format       # Format and lint all code
just lint-backend # Ruff check
just fix-backend  # Ruff fix and format
```

### Build & Deploy
```bash
just build-backend   # Build SAM application
just build-frontend  # Production build
sam deploy --guided  # Deploy to AWS
```

## Local Development Configuration

### Environment Variables (local-env.json)
```json
{
  "KidsRewardsLambdaFunction": {
    "DYNAMODB_ENDPOINT_OVERRIDE": "http://dynamodb-local:8000",
    "USERS_TABLE_NAME": "KidsRewardsUsers",
    "STORE_ITEMS_TABLE_NAME": "KidsRewardsStoreItems",
    "PURCHASE_LOGS_TABLE_NAME": "KidsRewardsPurchaseLogs",
    "CHORES_TABLE_NAME": "KidsRewardsChores",
    "CHORE_LOGS_TABLE_NAME": "KidsRewardsChoreLogs",
    "REQUESTS_TABLE_NAME": "KidsRewardsRequests",
    "APP_SECRET_KEY": "random_testing_app_secret_key_for_local_development"
  }
}
```

### Critical Network Configuration
- Backend and DynamoDB run in Docker containers on `kidsrewards-network`
- Containers communicate using container names (e.g., `dynamodb-local:8000`)
- Frontend runs natively on host, accesses backend at `localhost:3000`

### Port Assignments
- **3000**: Backend API (SAM Local)
- **3001**: Frontend (React dev server - must set PORT=3001)
- **8000**: DynamoDB Local

## Test Credentials
- Parent: `testparent` / `password456`
- Kid: `testkid` / `password123`

## Key Implementation Details

### Authentication Flow
1. POST `/token` with username/password form data
2. Returns JWT token valid for 30 minutes
3. Frontend stores in localStorage and adds to Authorization header
4. Backend validates token and extracts user via `get_current_user` dependency

### Role-Based Access
- Parent role required for: creating chores, managing store, approving purchases, promoting users
- Kid role: can complete chores, request purchases, view own data
- Role check via `get_current_parent_user` dependency in FastAPI

### Database Schema Patterns
- All tables use UUID for primary keys (id field)
- Timestamps stored as ISO 8601 strings
- Points/costs stored as integers
- Global Secondary Indexes for query patterns (e.g., UserIdTimestampIndex)

### Frontend API Integration
- Axios interceptor automatically adds auth token
- API_URL defaults to production, proxies to localhost:3000 in development
- All API calls in services/api.ts with TypeScript interfaces

### Testing Requirements
- Backend: pytest with APP_SECRET_KEY environment variable set
- Frontend: React Testing Library for unit tests, Playwright for E2E
- Pre-commit hook runs Ruff and pytest automatically

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
3. Initialize table resource in crud.py
4. Update just db-create-tables command in Justfile
5. Add CRUD operations for new entity

### Run Single Test
```bash
# Backend
cd backend && pytest tests/test_specific.py::test_function_name

# Frontend
cd frontend && npm test -- --testNamePattern="test description"
```

## Troubleshooting

### Login 500 Error
- Usually DynamoDB connection issue
- Check DYNAMODB_ENDPOINT_OVERRIDE in local-env.json
- Should be `http://dynamodb-local:8000` for Docker network

### Port Conflicts
- Frontend MUST run on 3001 (backend uses 3000)
- Set with: `PORT=3001 npm start`

### Container Issues
- Use `docker ps -a` to check container status
- `docker start dynamodb-local` if container exists but stopped
- `docker rm dynamodb-local` to remove and recreate

## CI/CD Pipeline

### GitHub Actions (ci-tests.yml)
- Triggers on push/PR to main and feature branches
- Runs Ruff linting and formatting checks
- Executes pytest with coverage
- Tests frontend build

### Pre-commit Hook
- Automatically runs on git commit
- Checks only changed files
- Runs Ruff and pytest for backend
- Can be run manually: `just pre-commit`

### Production Deployment
- AWS Lambda via SAM for backend
- AWS Amplify for frontend
- ECR for Docker images
- GitHub Actions for automated deployment on main branch