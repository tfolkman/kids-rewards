# Kids Rewards Development Commands
# Run `just` to see all available commands

# Default recipe shows all available commands
default:
    @echo "🚀 Kids Rewards Development Commands"
    @echo "===================================="
    @echo ""
    @echo "Quick Start:"
    @echo "  just start-dev  (or 'just dev')  - Start complete dev environment with auto-reload"
    @echo "  just stop-dev   (or 'just stop') - Stop all development services"
    @echo ""
    @echo "All available commands:"
    @just --list --unsorted

# === Environment Setup ===

# Complete development environment setup with auto-reload
start-dev:
    #!/usr/bin/env bash
    set -e
    
    echo "🚀 Starting Kids Rewards Development Environment..."
    echo "================================================"
    
    # Step 1: Check prerequisites
    echo ""
    echo "📋 Checking prerequisites..."
    command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
    command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed. Aborting." >&2; exit 1; }
    command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }
    command -v sam >/dev/null 2>&1 || { echo "❌ AWS SAM CLI is required but not installed. Aborting." >&2; exit 1; }
    command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed. Aborting." >&2; exit 1; }
    echo "✅ All prerequisites installed"
    
    # Step 2: Setup Python environment with uv (if available) or fallback to venv
    echo ""
    echo "🐍 Setting up Python environment..."
    if command -v uv >/dev/null 2>&1; then
        if [ ! -d ".venv" ] || [ ! -f ".venv/bin/activate" ]; then
            echo "Creating virtual environment with uv..."
            uv venv .venv
        fi
        echo "✅ Virtual environment ready (using uv)"
    else
        if [ ! -d ".venv" ]; then
            echo "Creating virtual environment with standard venv..."
            python3 -m venv .venv
        fi
        echo "✅ Virtual environment ready (using standard venv)"
    fi
    
    # Step 3: Install dependencies
    echo ""
    echo "📦 Installing dependencies..."
    
    # Backend dependencies
    if command -v uv >/dev/null 2>&1; then
        echo "Installing backend dependencies with uv..."
        source .venv/bin/activate && cd backend && uv pip install -r requirements.txt && cd ..
    else
        echo "Installing backend dependencies with pip..."
        source .venv/bin/activate && cd backend && pip install -r requirements.txt && cd ..
    fi
    
    # Frontend dependencies (only if node_modules doesn't exist or package.json is newer)
    if [ ! -d "frontend/node_modules" ] || [ "frontend/package.json" -nt "frontend/node_modules" ]; then
        echo "Installing frontend dependencies..."
        cd frontend && npm install && cd ..
    else
        echo "Frontend dependencies already up to date"
    fi
    echo "✅ All dependencies installed"
    
    # Step 4: Start DynamoDB
    echo ""
    echo "🗄️ Starting DynamoDB local..."
    # Handle existing container properly
    if docker ps -a --format '{{{{.Names}}' | grep -q '^dynamodb-local$'; then
        if docker ps --format '{{{{.Names}}' | grep -q '^dynamodb-local$'; then
            echo "✅ DynamoDB local is already running"
        else
            echo "Starting existing DynamoDB container..."
            docker start dynamodb-local
            echo "✅ DynamoDB local container restarted"
        fi
    else
        echo "Creating new DynamoDB container..."
        docker network create kidsrewards-network 2>/dev/null || true
        mkdir -p data
        docker run --name dynamodb-local \
            --network kidsrewards-network \
            -p 8000:8000 \
            -v "$(pwd)/data:/home/dynamodblocal/data" \
            -d \
            amazon/dynamodb-local \
            -jar DynamoDBLocal.jar -sharedDb -dbPath ./data
        echo "✅ DynamoDB local container created and started"
    fi
    
    # Wait for DynamoDB to be ready
    echo "Waiting for DynamoDB to be ready..."
    for i in {1..30}; do
        if aws dynamodb list-tables --endpoint-url http://localhost:8000 >/dev/null 2>&1; then
            echo "✅ DynamoDB is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ DynamoDB failed to start after 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    # Step 5: Create tables
    echo ""
    echo "📊 Setting up database tables..."
    just db-create-tables
    
    # Step 6: Build SAM application
    echo ""
    echo "🔨 Building SAM application..."
    cd backend && sam build -t template.yaml && cd ..
    echo "✅ SAM application built"
    
    # Step 7: Start services with auto-reload
    echo ""
    echo "🎯 Starting services with auto-reload..."
    echo "================================================"
    
    # Check if tmux is available
    if command -v tmux &> /dev/null; then
        # Kill existing session if it exists
        tmux kill-session -t kids-rewards 2>/dev/null || true
        
        # Create new tmux session
        tmux new-session -d -s kids-rewards -n "Kids Rewards Dev"
        
        # Split into 3 panes
        tmux split-window -h -t kids-rewards
        tmux split-window -v -t kids-rewards
        
        # Start backend with auto-reload in first pane
        tmux send-keys -t kids-rewards:0.0 "sam local start-api -t backend/template.yaml \\
            --env-vars local-env.json \\
            --docker-network kidsrewards-network \\
            --warm-containers LAZY \\
            --parameter-overrides \"AppImageUri=kidsrewardslambdafunction:latest TableNamePrefix=local- LocalDynamoDBEndpoint=http://localhost:8000\"" Enter
        
        # Start frontend with hot-reload in second pane (on port 3001)
        tmux send-keys -t kids-rewards:0.1 "cd frontend && PORT=3001 npm start" Enter
        
        # Show status in third pane
        tmux send-keys -t kids-rewards:0.2 "just status" Enter
        
        echo ""
        echo "✅ Development environment started successfully!"
        echo ""
        echo "📍 Services are running at:"
        echo "   • Frontend: http://localhost:3001"
        echo "   • Backend API: http://localhost:3000"
        echo "   • DynamoDB: http://localhost:8000"
        echo ""
        echo "🔄 Auto-reload is enabled for both frontend and backend"
        echo ""
        echo "📺 To view the development session:"
        echo "   tmux attach -t kids-rewards"
        echo ""
        echo "🛑 To stop all services:"
        echo "   just stop-dev"
        echo ""
        echo "🔑 Test credentials:"
        echo "   • Parent: testparent / password456"
        echo "   • Kid: testkid / password123"
    else
        echo ""
        echo "⚠️  tmux not found. Starting services in background..."
        echo ""
        
        # Start backend in background
        sam local start-api -t backend/template.yaml \
            --env-vars local-env.json \
            --docker-network kidsrewards-network \
            --warm-containers LAZY \
            --parameter-overrides "AppImageUri=kidsrewardslambdafunction:latest TableNamePrefix=local- LocalDynamoDBEndpoint=http://localhost:8000" \
            > backend.log 2>&1 &
        BACKEND_PID=$!
        echo "Backend started (PID: $BACKEND_PID, logs: backend.log)"
        
        # Start frontend in background (on port 3001)
        cd frontend && PORT=3001 npm start > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
        echo "Frontend started (PID: $FRONTEND_PID, logs: frontend.log)"
        
        # Save PIDs for stop-dev command
        echo $BACKEND_PID > .backend.pid
        echo $FRONTEND_PID > .frontend.pid
        
        echo ""
        echo "✅ Development environment started successfully!"
        echo ""
        echo "📍 Services are running at:"
        echo "   • Frontend: http://localhost:3001"
        echo "   • Backend API: http://localhost:3000"
        echo "   • DynamoDB: http://localhost:8000"
        echo ""
        echo "🔄 Auto-reload is enabled for both frontend and backend"
        echo ""
        echo "📝 View logs:"
        echo "   • Backend: tail -f backend.log"
        echo "   • Frontend: tail -f frontend.log"
        echo ""
        echo "🛑 To stop all services:"
        echo "   just stop-dev"
        echo ""
        echo "🔑 Test credentials:"
        echo "   • Parent: testparent / password456"
        echo "   • Kid: testkid / password123"
    fi

# Install all dependencies (backend and frontend)
install:
    #!/usr/bin/env bash
    echo "Installing backend dependencies..."
    if command -v uv >/dev/null 2>&1; then
        if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate && cd backend && uv pip install -r requirements.txt && cd ..
        else
            cd backend && uv pip install -r requirements.txt && cd ..
        fi
        echo "✅ Backend dependencies installed with uv"
    else
        if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate && cd backend && pip install -r requirements.txt && cd ..
        else
            cd backend && pip install -r requirements.txt && cd ..
        fi
        echo "✅ Backend dependencies installed with pip"
    fi
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    echo "✅ All dependencies installed!"

# Create/activate Python virtual environment (using uv if available)
venv:
    #!/usr/bin/env bash
    if command -v uv >/dev/null 2>&1; then
        echo "Creating Python virtual environment with uv..."
        uv venv .venv
        echo "✅ Virtual environment created at .venv (using uv)"
    else
        echo "Creating Python virtual environment with standard venv..."
        python3 -m venv .venv
        echo "✅ Virtual environment created at .venv (using standard venv)"
    fi
    echo "To activate: source .venv/bin/activate (Linux/Mac) or .venv\\Scripts\\activate (Windows)"

# === Backend Commands ===

# Start backend API with SAM local (requires Docker)
backend:
    @echo "Starting backend API with SAM local..."
    sam local start-api -t backend/template.yaml \
        --env-vars local-env.json \
        --docker-network kidsrewards-network \
        --parameter-overrides "AppImageUri=kidsrewardslambdafunction:latest TableNamePrefix=local- LocalDynamoDBEndpoint=http://localhost:8000"

# Start backend API with uvicorn (faster, no Docker required - use if SAM has issues)
backend-uvicorn:
    @echo "Starting backend API with uvicorn (no Docker required)..."
    cd backend && source venv/bin/activate 2>/dev/null || source ../venv/bin/activate 2>/dev/null || source ../.venv/bin/activate 2>/dev/null || true && \
    DYNAMODB_ENDPOINT_OVERRIDE=http://localhost:8000 \
    USERS_TABLE_NAME=KidsRewardsUsers \
    STORE_ITEMS_TABLE_NAME=KidsRewardsStoreItems \
    PURCHASE_LOGS_TABLE_NAME=KidsRewardsPurchaseLogs \
    CHORES_TABLE_NAME=KidsRewardsChores \
    CHORE_LOGS_TABLE_NAME=KidsRewardsChoreLogs \
    REQUESTS_TABLE_NAME=KidsRewardsRequests \
    CHORE_ASSIGNMENTS_TABLE_NAME=KidsRewardsChoreAssignments \
    PETS_TABLE_NAME=KidsRewardsPets \
    PET_CARE_SCHEDULES_TABLE_NAME=KidsRewardsPetCareSchedules \
    PET_CARE_TASK_INSTANCES_TABLE_NAME=KidsRewardsPetCareTasks \
    PET_HEALTH_LOGS_TABLE_NAME=KidsRewardsPetHealthLogs \
    APP_SECRET_KEY=random_testing_app_secret_key_for_local_development \
    uvicorn main:app --host 0.0.0.0 --port 3000 --reload

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
    @echo "Starting frontend development server on port 3001..."
    cd frontend && PORT=3001 npm start

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
    cd frontend && npx playwright test

# Run Playwright E2E tests with UI
e2e-ui:
    @echo "Running Playwright E2E tests with UI..."
    cd frontend && npx playwright test --ui

# Show Playwright test report
e2e-report:
    @echo "Opening Playwright test report..."
    cd frontend && npx playwright show-report

# Run specific E2E test file
e2e-file file:
    @echo "Running E2E test: {{file}}..."
    cd frontend && npx playwright test {{file}}

# Run E2E tests for chore submission
e2e-chores:
    @echo "Running chore submission E2E tests..."
    cd frontend && npx playwright test chore-submission.spec.ts --reporter=list

# Run E2E tests in headed mode (visible browser)
e2e-headed:
    @echo "Running E2E tests with visible browser..."
    cd frontend && npx playwright test --headed

# Run E2E tests for a specific browser
e2e-chrome:
    @echo "Running E2E tests on Chrome only..."
    cd frontend && npx playwright test --project=chromium

e2e-firefox:
    @echo "Running E2E tests on Firefox only..."
    cd frontend && npx playwright test --project=firefox

e2e-safari:
    @echo "Running E2E tests on Safari/WebKit only..."
    cd frontend && npx playwright test --project=webkit

# Debug a specific E2E test
e2e-debug test:
    @echo "Debugging E2E test: {{test}}..."
    cd frontend && npx playwright test {{test}} --debug

# Install Playwright browsers if needed
e2e-install:
    @echo "Installing Playwright browsers..."
    cd frontend && npx playwright install

# === Combined Commands ===

# Run all tests (backend and frontend)
test: test-backend test-frontend
    @echo "✅ All tests completed!"

# Format and lint all code
format: format-backend lint-backend
    @echo "✅ All code formatted and linted!"

# Legacy dev command - now use start-dev instead
dev-legacy:
    @echo "Starting full development environment..."
    @echo "This requires multiple terminals. Run these commands in separate terminals:"
    @echo "  1. just backend   (for backend API)"
    @echo "  2. just frontend  (for frontend)"
    @echo ""
    @echo "Or use 'just dev-tmux' if you have tmux installed"

# Start development environment with tmux (if available) - DEPRECATED: use start-dev instead
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

# Create all DynamoDB tables if they don't exist
db-create-tables:
    #!/usr/bin/env bash
    echo "Creating DynamoDB tables if they don't exist..."
    # Check if tables exist first
    existing_tables=$(aws dynamodb list-tables --endpoint-url http://localhost:8000 --output json 2>/dev/null | jq -r '.TableNames[]' 2>/dev/null || echo "")
    
    # KidsRewardsUsers table
    if echo "$existing_tables" | grep -q "KidsRewardsUsers"; then
        echo "✓ KidsRewardsUsers table already exists"
    else
        echo "Creating KidsRewardsUsers table..."
        aws dynamodb create-table \
            --table-name KidsRewardsUsers \
            --attribute-definitions AttributeName=username,AttributeType=S \
            --key-schema AttributeName=username,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsUsers"
    fi
    
    # KidsRewardsStoreItems table
    if echo "$existing_tables" | grep -q "KidsRewardsStoreItems"; then
        echo "✓ KidsRewardsStoreItems table already exists"
    else
        echo "Creating KidsRewardsStoreItems table..."
        aws dynamodb create-table \
            --table-name KidsRewardsStoreItems \
            --attribute-definitions AttributeName=id,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsStoreItems"
    fi
    
    # KidsRewardsPurchaseLogs table
    if echo "$existing_tables" | grep -q "KidsRewardsPurchaseLogs"; then
        echo "✓ KidsRewardsPurchaseLogs table already exists"
    else
        echo "Creating KidsRewardsPurchaseLogs table..."
        aws dynamodb create-table \
            --table-name KidsRewardsPurchaseLogs \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=user_id,AttributeType=S \
                AttributeName=timestamp,AttributeType=S \
                AttributeName=status,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --global-secondary-indexes \
                '[{"IndexName": "UserIdTimestampIndex","KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"},{"AttributeName": "timestamp", "KeyType": "RANGE"}],"Projection": {"ProjectionType": "ALL"},"ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}},{"IndexName": "StatusTimestampIndex","KeySchema": [{"AttributeName": "status", "KeyType": "HASH"},{"AttributeName": "timestamp", "KeyType": "RANGE"}],"Projection": {"ProjectionType": "ALL"},"ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsPurchaseLogs"
    fi
    
    # KidsRewardsChores table
    if echo "$existing_tables" | grep -q "KidsRewardsChores"; then
        echo "✓ KidsRewardsChores table already exists"
    else
        echo "Creating KidsRewardsChores table..."
        aws dynamodb create-table \
            --table-name KidsRewardsChores \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=created_by_parent_id,AttributeType=S \
                AttributeName=is_active,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --global-secondary-indexes \
                '[{"IndexName": "ParentChoresIndex","KeySchema": [{"AttributeName": "created_by_parent_id", "KeyType": "HASH"}],"Projection": {"ProjectionType": "ALL"},"ProvisionedThroughput": {"ReadCapacityUnits": 2, "WriteCapacityUnits": 2}},{"IndexName": "ActiveChoresIndex","KeySchema": [{"AttributeName": "is_active", "KeyType": "HASH"}],"Projection": {"ProjectionType": "ALL"},"ProvisionedThroughput": {"ReadCapacityUnits": 2, "WriteCapacityUnits": 2}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsChores"
    fi
    
    # KidsRewardsChoreLogs table
    if echo "$existing_tables" | grep -q "KidsRewardsChoreLogs"; then
        echo "✓ KidsRewardsChoreLogs table already exists"
    else
        echo "Creating KidsRewardsChoreLogs table..."
        aws dynamodb create-table \
            --table-name KidsRewardsChoreLogs \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=kid_id,AttributeType=S \
                AttributeName=submitted_at,AttributeType=S \
                AttributeName=status,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --global-secondary-indexes \
                '[{"IndexName": "KidChoreLogIndex","KeySchema": [{"AttributeName": "kid_id", "KeyType": "HASH"},{"AttributeName": "submitted_at", "KeyType": "RANGE"}],"Projection": {"ProjectionType": "ALL"},"ProvisionedThroughput": {"ReadCapacityUnits": 2, "WriteCapacityUnits": 2}},{"IndexName": "ChoreLogStatusIndex","KeySchema": [{"AttributeName": "status", "KeyType": "HASH"},{"AttributeName": "submitted_at", "KeyType": "RANGE"}],"Projection": {"ProjectionType": "ALL"},"ProvisionedThroughput": {"ReadCapacityUnits": 2, "WriteCapacityUnits": 2}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsChoreLogs"
    fi
    
    # KidsRewardsRequests table
    if echo "$existing_tables" | grep -q "KidsRewardsRequests"; then
        echo "✓ KidsRewardsRequests table already exists"
    else
        echo "Creating KidsRewardsRequests table..."
        aws dynamodb create-table \
            --table-name KidsRewardsRequests \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=requester_id,AttributeType=S \
                AttributeName=created_at,AttributeType=S \
                AttributeName=status,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --global-secondary-indexes \
                '[{"IndexName": "RequesterIdCreatedAtGSI","KeySchema": [{"AttributeName":"requester_id","KeyType":"HASH"}, {"AttributeName":"created_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":2,"WriteCapacityUnits":2}},{"IndexName": "StatusCreatedAtGSI","KeySchema": [{"AttributeName":"status","KeyType":"HASH"}, {"AttributeName":"created_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":2,"WriteCapacityUnits":2}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsRequests"
    fi

    # KidsRewardsChoreAssignments table
    if echo "$existing_tables" | grep -q "KidsRewardsChoreAssignments"; then
        echo "✓ KidsRewardsChoreAssignments table already exists"
    else
        echo "Creating KidsRewardsChoreAssignments table..."
        aws dynamodb create-table \
            --table-name KidsRewardsChoreAssignments \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=assigned_to_kid_id,AttributeType=S \
                AttributeName=due_date,AttributeType=S \
                AttributeName=assigned_by_parent_id,AttributeType=S \
                AttributeName=assignment_status,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --global-secondary-indexes \
                '[{"IndexName":"KidAssignmentsIndex","KeySchema":[{"AttributeName":"assigned_to_kid_id","KeyType":"HASH"},{"AttributeName":"due_date","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":2,"WriteCapacityUnits":2}},{"IndexName":"ParentAssignmentsIndex","KeySchema":[{"AttributeName":"assigned_by_parent_id","KeyType":"HASH"},{"AttributeName":"due_date","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":2,"WriteCapacityUnits":2}},{"IndexName":"StatusAssignmentsIndex","KeySchema":[{"AttributeName":"assignment_status","KeyType":"HASH"},{"AttributeName":"due_date","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":2,"WriteCapacityUnits":2}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsChoreAssignments"
    fi

    # KidsRewardsPets table (on-demand billing for cost optimization)
    if echo "$existing_tables" | grep -q "KidsRewardsPets"; then
        echo "✓ KidsRewardsPets table already exists"
    else
        echo "Creating KidsRewardsPets table..."
        aws dynamodb create-table \
            --table-name KidsRewardsPets \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=parent_id,AttributeType=S \
                AttributeName=is_active,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --global-secondary-indexes \
                '[{"IndexName":"ParentPetsIndex","KeySchema":[{"AttributeName":"parent_id","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}},{"IndexName":"ActivePetsIndex","KeySchema":[{"AttributeName":"is_active","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsPets"
    fi

    # KidsRewardsPetCareSchedules table (on-demand billing)
    if echo "$existing_tables" | grep -q "KidsRewardsPetCareSchedules"; then
        echo "✓ KidsRewardsPetCareSchedules table already exists"
    else
        echo "Creating KidsRewardsPetCareSchedules table..."
        aws dynamodb create-table \
            --table-name KidsRewardsPetCareSchedules \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=pet_id,AttributeType=S \
                AttributeName=is_active,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --global-secondary-indexes \
                '[{"IndexName":"PetSchedulesIndex","KeySchema":[{"AttributeName":"pet_id","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}},{"IndexName":"ActiveSchedulesIndex","KeySchema":[{"AttributeName":"is_active","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsPetCareSchedules"
    fi

    # KidsRewardsPetCareTasks table (on-demand billing)
    if echo "$existing_tables" | grep -q "KidsRewardsPetCareTasks"; then
        echo "✓ KidsRewardsPetCareTasks table already exists"
    else
        echo "Creating KidsRewardsPetCareTasks table..."
        aws dynamodb create-table \
            --table-name KidsRewardsPetCareTasks \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=assigned_to_kid_id,AttributeType=S \
                AttributeName=due_date,AttributeType=S \
                AttributeName=pet_id,AttributeType=S \
                AttributeName=status,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --global-secondary-indexes \
                '[{"IndexName":"KidTasksIndex","KeySchema":[{"AttributeName":"assigned_to_kid_id","KeyType":"HASH"},{"AttributeName":"due_date","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}},{"IndexName":"PetTasksIndex","KeySchema":[{"AttributeName":"pet_id","KeyType":"HASH"},{"AttributeName":"due_date","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}},{"IndexName":"TaskStatusIndex","KeySchema":[{"AttributeName":"status","KeyType":"HASH"},{"AttributeName":"due_date","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsPetCareTasks"
    fi

    # KidsRewardsPetHealthLogs table (on-demand billing)
    if echo "$existing_tables" | grep -q "KidsRewardsPetHealthLogs"; then
        echo "✓ KidsRewardsPetHealthLogs table already exists"
    else
        echo "Creating KidsRewardsPetHealthLogs table..."
        aws dynamodb create-table \
            --table-name KidsRewardsPetHealthLogs \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=pet_id,AttributeType=S \
                AttributeName=logged_at,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --global-secondary-indexes \
                '[{"IndexName":"PetHealthLogsIndex","KeySchema":[{"AttributeName":"pet_id","KeyType":"HASH"},{"AttributeName":"logged_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
            --endpoint-url http://localhost:8000 >/dev/null 2>&1 && echo "✓ Created KidsRewardsPetHealthLogs"
    fi

    echo "✅ All tables ready!"

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
    @-docker network create kidsrewards-network 2>/dev/null || true
    @echo "Creating data directory if it doesn't exist..."
    @mkdir -p data
    @echo "Checking if DynamoDB container already exists..."
    @if docker ps -a --format '{{{{.Names}}' | grep -q '^dynamodb-local$$'; then \
        if docker ps --format '{{{{.Names}}' | grep -q '^dynamodb-local$$'; then \
            echo "✅ DynamoDB local is already running"; \
        else \
            echo "Starting existing DynamoDB container..."; \
            docker start dynamodb-local >/dev/null 2>&1; \
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
            -jar DynamoDBLocal.jar -sharedDb -dbPath ./data >/dev/null 2>&1; \
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

# Stop all development services
stop-dev:
    #!/usr/bin/env bash
    echo "🛑 Stopping Kids Rewards Development Environment..."
    # Stop tmux session if it exists
    if tmux has-session -t kids-rewards 2>/dev/null; then
        echo "Stopping tmux session..."
        tmux kill-session -t kids-rewards
        echo "✅ Tmux session stopped"
    fi
    # Stop background processes if PIDs exist
    if [ -f .backend.pid ]; then
        PID=$(cat .backend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping backend (PID: $PID)..."
            kill $PID
        fi
        rm .backend.pid
    fi
    if [ -f .frontend.pid ]; then
        PID=$(cat .frontend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping frontend (PID: $PID)..."
            kill $PID
        fi
        rm .frontend.pid
    fi
    # Also try to kill any remaining SAM/npm processes
    pkill -f "sam local start-api" 2>/dev/null || true
    pkill -f "npm start" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    echo "✅ All application services stopped"
    echo ""
    echo "📝 Note: DynamoDB is still running. To stop it:"
    echo "   just db-stop"
    echo ""
    echo "To restart development:"
    echo "   just start-dev"

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
bu: backend-uvicorn
f: frontend
t: test
fmt: format
dev: start-dev
stop: stop-dev

# Simple dev setup - starts DynamoDB + instructions for terminals
dev-simple:
    #!/usr/bin/env bash
    echo "🚀 Simple Dev Environment Setup"
    echo "================================"
    echo ""

    # Check and start DynamoDB
    if ! curl -s http://localhost:8000 >/dev/null 2>&1; then
        echo "Starting DynamoDB..."
        just db-start-detached
        sleep 3
        just db-create-tables
    else
        echo "✅ DynamoDB already running"
    fi

    echo ""
    echo "📋 Start these commands in separate terminals:"
    echo ""
    echo "  Terminal 1 (Backend):  just backend"
    echo "  Terminal 2 (Frontend): just frontend"
    echo ""
    echo "💡 If SAM has Docker issues, use: just backend-uvicorn"
    echo ""
    echo "🔑 Test credentials:"
    echo "   • Parent: testparent / password456"
    echo "   • Kid: testkid / password123"
    echo ""
    echo "📍 URLs:"
    echo "   • Frontend: http://localhost:3001"
    echo "   • Backend:  http://localhost:3000"
    echo "   • API Docs: http://localhost:3000/docs"