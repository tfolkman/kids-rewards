# Kids Rewards Development Commands
# Run `just` to see all available commands

# Default recipe shows all available commands
default:
    @just --list --unsorted

# === Environment Setup ===

# Install all dependencies (backend and frontend)
install:
    @echo "Installing backend dependencies..."
    cd backend && pip install -r requirements.txt
    @echo "Installing frontend dependencies..."
    cd frontend && npm install
    @echo "✅ All dependencies installed!"

# Create/activate Python virtual environment
venv:
    @echo "Creating Python virtual environment..."
    python -m venv .venv
    @echo "✅ Virtual environment created at .venv"
    @echo "To activate: source .venv/bin/activate (Linux/Mac) or .venv\\Scripts\\activate (Windows)"

# === Backend Commands ===

# Start backend API with SAM local
backend:
    @echo "Starting backend API with SAM local..."
    sam local start-api -t backend/template.yaml \
        --env-vars local-env.json \
        --docker-network kidsrewards-network \
        --parameter-overrides "AppImageUri=kidsrewardslambdafunction:latest TableNamePrefix=local- LocalDynamoDBEndpoint=http://localhost:8000"

# Build SAM application
build-backend:
    @echo "Building SAM application..."
    sam build -t backend/template.yaml

# Run backend tests
test-backend:
    @echo "Running backend tests..."
    cd backend && APP_SECRET_KEY="test-secret-key-for-pre-commit-hook-validation-32chars" pytest

# Run backend tests with coverage
test-backend-coverage:
    @echo "Running backend tests with coverage..."
    cd backend && APP_SECRET_KEY="test-secret-key-for-pre-commit-hook-validation-32chars" pytest --cov

# Lint backend code with Ruff
lint-backend:
    @echo "Linting backend code..."
    cd backend && ruff check .

# Format backend code with Ruff
format-backend:
    @echo "Formatting backend code..."
    cd backend && ruff format .

# Fix backend linting issues and format
fix-backend:
    @echo "Fixing backend issues..."
    cd backend && ruff check . --fix && ruff format .

# === Frontend Commands ===

# Start frontend development server
frontend:
    @echo "Starting frontend development server..."
    cd frontend && npm start

# Build frontend for production
build-frontend:
    @echo "Building frontend for production..."
    cd frontend && npm run build

# Run frontend unit tests
test-frontend:
    @echo "Running frontend unit tests..."
    cd frontend && npm test -- --watchAll=false

# Run frontend tests in watch mode
test-frontend-watch:
    @echo "Running frontend tests in watch mode..."
    cd frontend && npm test

# Run Playwright E2E tests
e2e:
    @echo "Running Playwright E2E tests..."
    cd frontend && npm run e2e

# Run Playwright E2E tests with UI
e2e-ui:
    @echo "Running Playwright E2E tests with UI..."
    cd frontend && npm run e2e:ui

# Show Playwright test report
e2e-report:
    @echo "Opening Playwright test report..."
    cd frontend && npm run e2e:report

# === Combined Commands ===

# Run all tests (backend and frontend)
test: test-backend test-frontend
    @echo "✅ All tests completed!"

# Format and lint all code
format: format-backend lint-backend
    @echo "✅ All code formatted and linted!"

# Start both backend and frontend (requires two terminal tabs)
dev:
    @echo "Starting full development environment..."
    @echo "This requires multiple terminals. Run these commands in separate terminals:"
    @echo "  1. just backend   (for backend API)"
    @echo "  2. just frontend  (for frontend)"
    @echo ""
    @echo "Or use 'just dev-tmux' if you have tmux installed"

# Start development environment with tmux (if available)
dev-tmux:
    #!/usr/bin/env bash
    if command -v tmux &> /dev/null; then
        tmux new-session -d -s kids-rewards
        tmux send-keys -t kids-rewards "just backend" Enter
        tmux split-window -h -t kids-rewards
        tmux send-keys -t kids-rewards "just frontend" Enter
        tmux attach -t kids-rewards
    else
        echo "tmux not found. Please install tmux or run 'just backend' and 'just frontend' in separate terminals"
    fi

# === Git Commands ===

# Run pre-commit checks manually
pre-commit:
    @echo "Running pre-commit checks..."
    @bash .git/hooks/pre-commit

# Quick commit with pre-commit checks
commit message:
    @echo "Committing with message: {{message}}"
    git add -A
    git commit -m "{{message}}"

# === Utility Commands ===

# Check if all services are running
status:
    @echo "Checking service status..."
    @echo -n "Backend API: "
    @curl -s http://localhost:3000/health 2>/dev/null && echo "✅ Running" || echo "❌ Not running"
    @echo -n "Frontend: "
    @curl -s http://localhost:3001 2>/dev/null && echo "✅ Running" || echo "❌ Not running"
    @echo -n "DynamoDB Local: "
    @curl -s http://localhost:8000 2>/dev/null && echo "✅ Running" || echo "❌ Not running"

# Clean build artifacts and caches
clean:
    @echo "Cleaning build artifacts..."
    rm -rf backend/.aws-sam
    rm -rf backend/htmlcov
    rm -rf backend/.coverage
    rm -rf backend/__pycache__
    rm -rf backend/**/__pycache__
    rm -rf frontend/build
    rm -rf frontend/coverage
    rm -rf frontend/playwright-report
    @echo "✅ Clean complete!"

# Show logs for backend
logs-backend:
    @echo "Showing backend logs..."
    docker logs -f $(docker ps --filter "ancestor=kidsrewardslambdafunction:latest" -q)

# Install pre-commit hook
install-hook:
    @echo "Installing pre-commit hook..."
    @chmod +x .git/hooks/pre-commit
    @echo "✅ Pre-commit hook installed!"

# === Docker/Database Commands ===

# Start DynamoDB local (following README instructions)
db-start:
    @echo "Starting DynamoDB local..."
    @echo "Creating Docker network if it doesn't exist..."
    -docker network create kidsrewards-network 2>/dev/null || true
    @echo "Creating data directory if it doesn't exist..."
    mkdir -p data
    @echo "Checking if DynamoDB container already exists..."
    @if docker ps -a --format '{{{{.Names}}' | grep -q '^dynamodb-local$$'; then \
        if docker ps --format '{{{{.Names}}' | grep -q '^dynamodb-local$$'; then \
            echo "✅ DynamoDB local is already running"; \
            echo "To see logs, run: docker logs -f dynamodb-local"; \
        else \
            echo "Starting existing DynamoDB container..."; \
            docker start dynamodb-local && docker logs -f dynamodb-local; \
        fi \
    else \
        echo "Creating new DynamoDB container..."; \
        docker run --name dynamodb-local \
            --network kidsrewards-network \
            -p 8000:8000 \
            -v "$$(pwd)/data:/home/dynamodblocal/data" \
            amazon/dynamodb-local \
            -jar DynamoDBLocal.jar -sharedDb -dbPath ./data; \
    fi

# Start DynamoDB local in detached mode (background)
db-start-detached:
    @echo "Starting DynamoDB local in background..."
    @echo "Creating Docker network if it doesn't exist..."
    -docker network create kidsrewards-network 2>/dev/null || true
    @echo "Creating data directory if it doesn't exist..."
    mkdir -p data
    @echo "Checking if DynamoDB container already exists..."
    @if docker ps -a --format '{{{{.Names}}' | grep -q '^dynamodb-local$$'; then \
        if docker ps --format '{{{{.Names}}' | grep -q '^dynamodb-local$$'; then \
            echo "✅ DynamoDB local is already running"; \
        else \
            echo "Starting existing DynamoDB container..."; \
            docker start dynamodb-local; \
            echo "✅ DynamoDB local container restarted"; \
        fi \
    else \
        echo "Creating new DynamoDB container..."; \
        docker run --name dynamodb-local \
            --network kidsrewards-network \
            -p 8000:8000 \
            -v "$$(pwd)/data:/home/dynamodblocal/data" \
            -d \
            amazon/dynamodb-local \
            -jar DynamoDBLocal.jar -sharedDb -dbPath ./data; \
        echo "✅ DynamoDB local is running in background on port 8000"; \
    fi

# Stop DynamoDB local
db-stop:
    @echo "Stopping DynamoDB local..."
    docker stop dynamodb-local

# Remove DynamoDB container
db-remove:
    @echo "Removing DynamoDB container..."
    docker rm dynamodb-local

# List DynamoDB tables
db-list:
    @echo "Listing DynamoDB tables..."
    aws dynamodb list-tables --endpoint-url http://localhost:8000

# === Help Commands ===

# Show environment setup instructions
help-setup:
    @echo "Environment Setup Instructions:"
    @echo "================================"
    @echo "1. Create virtual environment: just venv"
    @echo "2. Activate it: source .venv/bin/activate"
    @echo "3. Install dependencies: just install"
    @echo "4. Start backend: just backend"
    @echo "5. Start frontend: just frontend"
    @echo ""
    @echo "Test credentials:"
    @echo "  Parent: testparent / password456"
    @echo "  Kid: testkid / password123"

# Quick health check of all services
health:
    @echo "Health Check Report"
    @echo "==================="
    @just status
    @echo ""
    @echo "Python version: $(python --version 2>&1)"
    @echo "Node version: $(node --version)"
    @echo "NPM version: $(npm --version)"
    @echo "Docker version: $(docker --version)"
    @echo "SAM CLI version: $(sam --version)"

# === Shortcuts ===

# Shortcuts for common commands
b: backend
f: frontend
t: test
fmt: format