# Kids Rewards Project

Welcome to the Kids Rewards project! This guide will help you understand how to set up and work with the project in different environments: local development and production.

## ✨ Features

### For Kids:
- **Points System**: Earn points by completing chores
- **Streak Tracking**: NEW! Build daily streaks by completing chores consistently
  - Visual streak counter with fire icon 🔥
  - Bonus points at milestones (3, 7, 14, 30 days)
  - Track current and longest streaks
  - Get reminders when streaks are at risk
- **Store**: Redeem points for rewards (requires parent approval)
- **Leaderboard**: See how you rank against siblings
- **Chore Management**: View available chores, assigned chores, and submit completions
- **Request System**: Request new store items or chores
- **Gemini AI Assistant**: Get smart suggestions for items and chores

### For Parents:
- **User Management**: Promote users to parent role
- **Store Management**: Add, edit, or remove store items
- **Chore Creation**: Create and manage chores with point values
- **Chore Assignment**: Assign specific chores to kids with due dates
- **Approval System**: Approve/reject purchase requests and chore completions
- **Points Awards**: Give bonus points with reasons
- **Request Management**: Review and approve kid requests for new items/chores

## 🚀 Quick Start: Local Development

### Prerequisites

Make sure you have these tools installed:

*   **Docker Desktop** - For running DynamoDB locally
*   **Python 3.12+** - Backend language
*   **Node.js & npm** - For the frontend
*   **AWS CLI** - For database operations
*   **AWS SAM CLI** - For running the backend locally
*   **Just** - Command runner (install via `brew install just` on Mac, or see [installation guide](https://github.com/casey/just#installation))

### 🎯 Super Quick Start

With the new simplified setup, you can start everything with a single command:

```bash
# Start the complete development environment
just dev

# Or use the full command name
just start-dev
```

This single command will:
- ✅ Check all prerequisites (Docker, Python, Node.js, AWS CLI, SAM CLI)
- ✅ Set up Python virtual environment (using `uv` if available for faster installs)
- ✅ Install all dependencies automatically
- ✅ Start DynamoDB local database
- ✅ Create all required database tables
- ✅ Build the SAM application
- ✅ Launch backend API and frontend with auto-reload enabled
- ✅ Use tmux for better terminal management (or background processes if tmux not available)

Then open http://localhost:3001 in your browser!

**Test Login Credentials:**
*   Parent: `testparent` / `password456`
*   Kid: `testkid` / `password123`

### Alternative Setup Methods

If you prefer to set up components individually or need to troubleshoot:

#### Manual Component Setup

1.  **Start Your Local Database:**
    ```bash
    just db-start-detached
    ```
    This starts DynamoDB in a Docker container with all the necessary configuration.

2.  **Create Your Database Tables:**
    ```bash
    # Automatically create all tables
    just db-create-tables
    
    # Or check existing tables
    just db-list
    ```
    
    # Note: Full table creation commands are available in the original setup,
    # but most users can skip this as tables are usually pre-created
    
    *   **Create the `KidsRewardsStoreItems` table (if needed):**
        Assuming `local-store-items-table` for store items:
        ```bash
        aws dynamodb create-table \
            --table-name local-store-items-table \
            --attribute-definitions AttributeName=id,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --endpoint-url http://localhost:8000
        ```
    *   **Create the `KidsRewardsPurchaseLogs` table (or your configured local table name):**
        Assuming `KidsRewardsPurchaseLogs` for purchase logs:
        ```bash
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
                "[
                    {
                        \"IndexName\": \"UserIdTimestampIndex\",
                        \"KeySchema\": [
                            {\"AttributeName\": \"user_id\", \"KeyType\": \"HASH\"},
                            {\"AttributeName\": \"timestamp\", \"KeyType\": \"RANGE\"}
                        ],
                        \"Projection\": {\"ProjectionType\": \"ALL\"},
                        \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 5, \"WriteCapacityUnits\": 5}
                    },
                    {
                        \"IndexName\": \"StatusTimestampIndex\",
                        \"KeySchema\": [
                            {\"AttributeName\": \"status\", \"KeyType\": \"HASH\"},
                            {\"AttributeName\": \"timestamp\", \"KeyType\": \"RANGE\"}
                        ],
                        \"Projection\": {\"ProjectionType\": \"ALL\"},
                        \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 5, \"WriteCapacityUnits\": 5}
                    }
                ]" \
            --endpoint-url http://localhost:8000
        ```
    *   **Create the `KidsRewardsChores` table (or your configured local table name):**
        Assuming `KidsRewardsChores` for chores:
        ```bash
        aws dynamodb create-table \
            --table-name KidsRewardsChores \
            --attribute-definitions \
                AttributeName=id,AttributeType=S \
                AttributeName=created_by_parent_id,AttributeType=S \
                AttributeName=is_active,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --global-secondary-indexes \
                "[
                    {
                        \"IndexName\": \"ParentChoresIndex\",
                        \"KeySchema\": [{\"AttributeName\": \"created_by_parent_id\", \"KeyType\": \"HASH\"}],
                        \"Projection\": {\"ProjectionType\": \"ALL\"},
                        \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 2, \"WriteCapacityUnits\": 2}
                    },
                    {
                        \"IndexName\": \"ActiveChoresIndex\",
                        \"KeySchema\": [{\"AttributeName\": \"is_active\", \"KeyType\": \"HASH\"}],
                        \"Projection\": {\"ProjectionType\": \"ALL\"},
                        \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 2, \"WriteCapacityUnits\": 2}
                    }
                ]" \
            --endpoint-url http://localhost:8000
        ```
    *   **Create the `KidsRewardsChoreLogs` table (or your configured local table name):**
        Assuming `KidsRewardsChoreLogs` for chore logs:
        ```bash
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
                "[
                    {
                        \"IndexName\": \"KidChoreLogIndex\",
                        \"KeySchema\": [
                            {\"AttributeName\": \"kid_id\", \"KeyType\": \"HASH\"},
                            {\"AttributeName\": \"submitted_at\", \"KeyType\": \"RANGE\"}
                        ],
                        \"Projection\": {\"ProjectionType\": \"ALL\"},
                        \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 2, \"WriteCapacityUnits\": 2}
                    },
                    {
                        \"IndexName\": \"ChoreLogStatusIndex\",
                        \"KeySchema\": [
                            {\"AttributeName\": \"status\", \"KeyType\": \"HASH\"},
                            {\"AttributeName\": \"submitted_at\", \"KeyType\": \"RANGE\"}
                        ],
                        \"Projection\": {\"ProjectionType\": \"ALL\"},
                        \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 2, \"WriteCapacityUnits\": 2}
                    }
                ]" \
            --endpoint-url http://localhost:8000
        ```
    *   **Create the `KidsRewardsRequests` table (or your configured local table name):**
        Assuming `KidsRewardsRequests` for feature requests:
        ```bash
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
                "[
                    {
                        \"IndexName\": \"RequesterIdCreatedAtGSI\",
                        \"KeySchema\": [{\"AttributeName\":\"requester_id\",\"KeyType\":\"HASH\"}, {\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}],
                        \"Projection\":{\"ProjectionType\":\"ALL\"},
                        \"ProvisionedThroughput\":{\"ReadCapacityUnits\":2,\"WriteCapacityUnits\":2}
                    },
                    {
                        \"IndexName\": \"StatusCreatedAtGSI\",
                        \"KeySchema\": [{\"AttributeName\":\"status\",\"KeyType\":\"HASH\"}, {\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}],
                        \"Projection\":{\"ProjectionType\":\"ALL\"},
                        \"ProvisionedThroughput\":{\"ReadCapacityUnits\":2,\"WriteCapacityUnits\":2}
                    }
                ]" \
            --endpoint-url http://localhost:8000
        ```
        *   `--endpoint-url http://localhost:8000` is very important! It tells the AWS CLI to talk to your *local* database, not the real one in the cloud.
        *   If you ever need to start fresh, you can delete these tables with `aws dynamodb delete-table --table-name YourTableName --endpoint-url http://localhost:8000` (e.g., for `KidsRewardsUsers`, `KidsRewardsStoreItems`, `KidsRewardsPurchaseLogs`, `KidsRewardsChores`, `KidsRewardsChoreLogs`, `KidsRewardsRequests`) and then run the `create-table` commands again.

3.  **Set up Python Environment:**
    ```bash
    # Create virtual environment (uses uv if available)
    just venv
    source .venv/bin/activate  # Mac/Linux
    # .venv\Scripts\activate   # Windows
    
    # Install all dependencies
    just install
    ```

4.  **Run Services Individually:**
    ```bash
    # Start backend API (port 3000)
    just backend
    
    # In another terminal, start frontend (port 3001)
    just frontend
    ```

### Development Commands

```bash
# Primary Commands
just dev              # Start complete dev environment (recommended)
just stop             # Stop all development services

# Service Management
just start-dev        # Full command name for starting everything
just stop-dev         # Full command name for stopping everything
just status           # Check if services are running
just health           # Full health check with versions

# Database Commands
just db-start-detached    # Start DynamoDB in background
just db-stop              # Stop DynamoDB
just db-create-tables     # Create all required tables
just db-list              # List existing tables

# Testing & Quality
just test             # Run all tests
just test-backend     # Backend tests only
just test-frontend    # Frontend tests only
just e2e              # End-to-end tests
just format           # Format and lint code
just pre-commit       # Run pre-commit checks

# Utility Commands
just clean            # Clean build artifacts
just logs-backend     # View backend logs
```

### Viewing Running Services

When using `just dev`, services run in tmux. To view them:

```bash
# Attach to tmux session
tmux attach -t kids-rewards

# Navigate between panes
Ctrl+B then arrow keys

# Detach from tmux (leave services running)
Ctrl+B then D
```

### Stopping Services

```bash
# Stop all application services
just stop

# Stop database as well
just db-stop
```

---

## 🧪 Testing and Linting

This project uses `pytest` for backend testing, React Testing Library and Playwright for frontend testing, and `Ruff` for Python linting and formatting.

### Quick Testing Commands

```bash
# Run all tests
just test

# Backend tests only
just test-backend

# Frontend tests only  
just test-frontend

# E2E tests with Playwright
just e2e

# Lint and format code
just format
```

### Backend (Python)

```bash
# Run tests with coverage
just test-backend-coverage

# Lint code
just lint-backend

# Auto-fix and format
just fix-backend
```
    *   **VS Code Integration for Ruff:**
        1.  Install the [Ruff VS Code extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff).
        2.  Enable "Format on Save" in VS Code settings:
            *   Open VS Code settings (File > Preferences > Settings or `Ctrl+,`).
            *   Search for "Format On Save" and check the box.
            *   Search for "Default Formatter" and select "Ruff" (`charliermarsh.ruff`) as the default formatter for Python files.
            *   You might want to add this to your workspace `.vscode/settings.json`:
                ```json
                {
                  "editor.formatOnSave": true,
                  "[python]": {
                    "editor.defaultFormatter": "charliermarsh.ruff",
                    "editor.codeActionsOnSave": {
                      "source.organizeImports": true // Optional: organize imports with Ruff
                    }
                  }
                }
                ```
        This will automatically format your Python files and organize imports when you save them.

The `just` commands automatically handle environment variables and paths for you. Coverage reports are generated in `backend/htmlcov/` and can be viewed by opening `backend/htmlcov/index.html` in a browser.

### Frontend (React/TypeScript)

```bash
# Run tests in watch mode
just test-frontend-watch

# Run E2E tests (make sure frontend is running first)
just frontend      # In terminal 1
just e2e           # In terminal 2

# Run E2E tests with UI for debugging
just e2e-ui

# View test report
just e2e-report
```

### CI/CD Automation

All tests and linting checks run automatically on every push or pull request via GitHub Actions. You can run the same checks locally with:

```bash
just pre-commit
```

This runs the exact same checks that GitHub will run, helping you catch issues before pushing.

---

## 🚀 Deployment to AWS (Production)

The production environment is where the live version of the application runs.

### How it Works

We use **GitHub Actions** to automate production deployments:

1.  **Trigger:** The workflow defined in `.github/workflows/aws-deploy.yml` is triggered automatically when code is pushed or merged into the `main` branch. It can also be triggered manually from the GitHub Actions tab.
2.  **Authentication:** The workflow uses AWS OIDC (OpenID Connect) to securely authenticate with your AWS account by assuming a pre-configured IAM Role. This avoids storing long-lived AWS credentials as GitHub secrets.
3.  **Backend Deployment:**
    *   The workflow checks out the code.
    *   It logs into Amazon ECR (Elastic Container Registry).
    *   It builds the Docker image for the backend application (from `backend/Dockerfile`).
    *   It pushes the tagged Docker image to your ECR repository.
    *   It then uses AWS SAM CLI (`sam deploy`) to deploy your backend stack. This command references your `backend/template.yaml`.
    *   The `sam deploy` command updates your AWS Lambda function to use the new Docker image from ECR and applies any changes to other resources defined in the template (like DynamoDB tables).
4.  **Frontend Deployment (AWS Amplify):**
    *   The production frontend is hosted on AWS Amplify.
    *   Amplify is configured to watch the `main` branch. When changes are pushed to `main`, Amplify automatically builds and deploys the latest version of the frontend.
    *   Ensure your Amplify app's build settings are correct and that it's configured to point to your production API Gateway endpoint.

### Prerequisites for Production Deployment

Before the GitHub Actions workflow can successfully deploy to production, you must have the following configured:

1.  **AWS IAM OIDC Role:**
    *   An IAM role must be created in your AWS account that trusts GitHub's OIDC provider.
    *   This role needs permissions to interact with ECR (push images), CloudFormation (deploy SAM stacks), S3 (for SAM artifacts), Lambda (update functions), DynamoDB (manage tables), and IAM (if your SAM template creates roles).
    *   The trust policy of this IAM role must be configured to allow your specific GitHub repository (e.g., `YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME`) and the `main` branch to assume it.
2.  **GitHub Secrets:**
    *   Navigate to your GitHub repository's "Settings" > "Secrets and variables" > "Actions".
    *   Add the following repository secrets:
        *   `AWS_ROLE_TO_ASSUME`: The ARN (Amazon Resource Name) of the IAM OIDC role created above (e.g., `arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/GitHubActionsDeployRole`).
        *   `SAM_S3_BUCKET_NAME`: The name of an S3 bucket in your AWS account (e.g., `us-west-2` region) where SAM CLI will store deployment artifacts. Create this bucket if it doesn't exist.
3.  **ECR Repository:**
    *   An ECR repository must exist with the name specified in the workflow (`kids-rewards-backend` by default, under registry `533984982271.dkr.ecr.us-west-2.amazonaws.com`). The workflow will push images here.

### Deploying to Production

1.  **Merge to Main:** Ensure your feature branch has been thoroughly tested (locally or via other means) and is ready to go live. Merge your changes into the `main` branch.
2.  **Monitor Deployment:** The GitHub Actions workflow "Deploy Backend to AWS" will automatically start. You can monitor its progress in the "Actions" tab of your GitHub repository.
3.  **Verify Production:** After the workflow completes successfully for both backend (GitHub Action) and frontend (Amplify), verify that the changes are live and functioning correctly in the production environment.

## \ud83d\udd27 Troubleshooting\n\n### Common Issues\n\n**DynamoDB Connection Error:**\n```bash\n# If backend can't connect to DynamoDB:\njust db-stop\njust db-start-detached\njust backend  # Restart backend\n```\n\n**Port Already in Use:**\n```bash\n# Check what's using the ports\nlsof -i :3000  # Backend port\nlsof -i :3001  # Frontend port\nlsof -i :8000  # DynamoDB port\n```\n\n**Container Already Exists:**\n```bash\n# The just command handles this automatically, but if needed:\ndocker rm dynamodb-local\njust db-start-detached\n```\n\n**Check Service Status:**\n```bash\njust status  # Shows status of all services\njust health  # Full health check with versions\n```\n\n## \ud83d\udcda Complete Command Reference\n\nFor a full list of available commands:\n```bash\njust --list\n```\n\nKey commands:\n- `just dev` - Instructions for starting full environment\n- `just install` - Install all dependencies\n- `just test` - Run all tests\n- `just format` - Format and lint code\n- `just clean` - Clean build artifacts\n\n## Next Steps & Important Notes

*   **Complete AWS Setup:** Ensure the IAM OIDC Role, GitHub Secrets (`AWS_ROLE_TO_ASSUME`, `SAM_S3_BUCKET_NAME`), and ECR repository are correctly set up as described in the "Prerequisites for Production Deployment" section.
*   **SAM S3 Bucket:** The `SAM_S3_BUCKET_NAME` secret should point to an S3 bucket you own, used by `sam deploy` for packaging.
*   **Amplify Configuration:** Double-check your AWS Amplify settings to ensure it's correctly building from the `main` branch and that its environment variables point to the production API Gateway endpoint. The API Gateway endpoint URL can be found in the outputs of your SAM stack after a successful deployment.
*   **Local Table Names:** The local setup instructions for creating DynamoDB tables and seeding use the default names (`KidsRewardsUsers`, `KidsRewardsStoreItems`, `KidsRewardsPurchaseLogs`, `KidsRewardsChores`, `KidsRewardsChoreLogs`, `KidsRewardsRequests`). Verify these against your `backend/template.yaml` (Conditions and Mappings for local environment) and `local-env.json` to ensure consistency if you've customized them.