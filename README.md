# Kids Rewards Project

A full-stack family chore and reward management app. Parents create chores and manage rewards, kids earn points by completing tasks.

## Features

### For Kids
- **Points System**: Earn points by completing chores
- **Streak Tracking**: Build daily streaks with bonus points at milestones
- **Store**: Redeem points for rewards (requires parent approval)
- **Leaderboard**: See rankings against siblings
- **Pet Care**: Complete assigned pet care tasks for points

### For Parents
- **Chore Management**: Create chores, assign to kids with due dates
- **Store Management**: Add/edit rewards
- **Approval System**: Approve/reject purchases and chore completions
- **Pet Care Module**: Manage pets, create care schedules, assign tasks
- **Points Awards**: Give bonus points with reasons

### Pet Care Module
- Add family pets with species, birthday, photos
- Create recurring care schedules (feeding, cleaning, exercise)
- Auto-generate daily tasks from schedules
- Assign care tasks to kids for points
- Track pet health (weight over time)

## Quick Start

### Prerequisites
- **Docker Desktop** - For running DynamoDB locally
- **Python 3.12+** - Backend
- **Node.js & npm** - Frontend
- **AWS CLI** - Database operations
- **AWS SAM CLI** - Running backend locally
- **Just** - Command runner (`brew install just` on Mac)

### Start Development Environment

```bash
# Option 1: Full automated setup (uses tmux)
just dev

# Option 2: Simple setup (manual terminals)
just dev-simple
```

Then open http://localhost:3001

**Test Credentials:**
- Parent: `testparent` / `password456`
- Kid: `testkid` / `password123`

### Manual Setup (if needed)

```bash
# 1. Start database
just db-start-detached
just db-create-tables

# 2. In terminal 1 - Start backend (port 3000)
just backend

# 3. In terminal 2 - Start frontend (port 3001)
just frontend
```

## Essential Commands

```bash
# Development
just dev              # Start everything with tmux
just dev-simple       # Start DynamoDB + show terminal instructions
just stop             # Stop all services

# Services
just backend          # Start backend (SAM local)
just backend-uvicorn  # Start backend (uvicorn - use if SAM has Docker issues)
just frontend         # Start frontend

# Database
just db-start-detached  # Start DynamoDB
just db-create-tables   # Create all tables
just db-list            # List tables

# Testing
just test             # All tests
just test-backend     # Backend tests (pytest)
just test-frontend    # Frontend tests (Jest)
just e2e              # E2E tests (Playwright)
just e2e-chrome       # E2E on Chrome only

# Code Quality
just format           # Format and lint
just pre-commit       # Run pre-commit checks
```

## Ports

| Service | Port |
|---------|------|
| Frontend | 3001 |
| Backend API | 3000 |
| DynamoDB Local | 8000 |

## Troubleshooting

### SAM "Docker not found" Error
Even when Docker is running, SAM sometimes can't detect it:
```bash
# Verify Docker works
docker ps

# Use uvicorn as alternative (no Docker needed)
just backend-uvicorn
```

### Login 500 Error
Usually a DynamoDB connection issue:
```bash
just db-start-detached  # Ensure DynamoDB is running
just db-list            # Verify tables exist
```

### Port Already in Use
```bash
lsof -i :3000  # Check what's using the port
lsof -i :3001
lsof -i :8000
```

### View Running Services
When using `just dev` with tmux:
```bash
tmux attach -t kids-rewards  # View session
# Ctrl+B then arrow keys to navigate
# Ctrl+B then D to detach
```

## Testing

```bash
# Run all tests
just test

# Backend tests with coverage
just test-backend-coverage

# E2E tests with visible browser
just e2e-headed

# E2E tests with UI debugger
just e2e-ui
```

## Project Structure

```
kids-rewards/
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── crud.py          # DynamoDB operations
│   ├── models.py        # Pydantic schemas
│   ├── security.py      # JWT/auth
│   └── template.yaml    # SAM template
├── frontend/
│   ├── src/
│   │   ├── App.tsx      # Main app + routes
│   │   ├── pages/       # Page components
│   │   ├── components/  # Shared components
│   │   └── services/    # API client
│   └── tests-e2e/       # Playwright tests
├── Justfile             # Development commands
├── CLAUDE.md            # AI assistant guide
└── local-env.json       # Local environment config
```

## Deployment

### GitHub Actions
- CI runs on push/PR to main and feature branches
- Runs linting, tests, and build verification

### Production
- **Backend**: AWS Lambda via SAM, deployed via GitHub Actions
- **Frontend**: AWS Amplify, auto-deploys from main branch

See `.github/workflows/` for CI/CD configuration.

## Contributing

1. Create feature branch from main
2. Make changes
3. Run `just pre-commit` before committing
4. Create PR to main

For detailed technical documentation, see [CLAUDE.md](CLAUDE.md).
