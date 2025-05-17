# Kids Rewards Project

Welcome to the Kids Rewards project! This guide will help you understand how to set up and work with the project in different environments: local development and production.

## 🚀 Getting Started: Local Development

This section explains how to run the backend (the "brain" of the app) and the frontend (what you see and interact with in the browser) on your own computer. This is great for making changes and testing things out!

### What You'll Need (Prerequisites)

Before you start, make sure you have these tools installed on your machine:

*   **Docker Desktop:** We use this to run a local version of our database (DynamoDB) and also to build and run our backend application locally via SAM CLI.
*   **Python:** The backend is written in Python (we're using version 3.12).
*   **pip:** Python's package installer (usually comes with Python).
*   **uv:** (Optional, but recommended for faster dependency management in Python) Can be installed via `pip install uv`.
*   **Node.js and npm:** Node.js is a JavaScript runtime, and npm is its package manager. We need these for the frontend. (npm usually comes with Node.js).
*   **AWS CLI:** The Amazon Web Services Command Line Interface. We'll use this to create our local database tables.
*   **AWS SAM CLI:** A tool from AWS that lets us run our serverless backend (Lambda functions and API Gateway) locally, just like it would run in the cloud.

### Setting up the Local Backend (The "Brain")

The backend handles all the logic, like user logins and managing points.

1.  **Start Your Local Database (DynamoDB Local with Docker):**
    Our app needs a database to store information. For local development, we'll run DynamoDB (the database AWS uses) inside a Docker container.

    *   **Open your Terminal (or Command Prompt/PowerShell on Windows).**
    *   **Create a Docker Network:** This helps our app's components talk to each other. You only need to do this once.
        ```bash
        docker network create kidsrewards-network
        ```
        (If it says `Error response from daemon: network with name kidsrewards-network already exists`, that's okay! It means you've already created it.)
    *   **Create a Folder for Database Data:** This folder will store your local database files so your data doesn't disappear when you stop the database.
        In your project's main folder (`kids_rewards`), if you don't already have a `data` folder, create it:
        ```bash
        mkdir data
        ```
    *   **Run DynamoDB Local:** This command starts the database container. Give it a specific name (`dynamodb-local`) and connect it to our network.
        ```bash
        docker run --name dynamodb-local --network kidsrewards-network -p 8000:8000 -v "$(pwd)/data:/home/dynamodblocal/data" amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb -dbPath ./data
        ```
        *   `--name dynamodb-local`: Gives our database container a friendly name.
        *   `--network kidsrewards-network`: Connects it to the network we created.
        *   `-p 8000:8000`: Makes the database accessible on port 8000 of your computer.
        *   `-v "$(pwd)/data:/home/dynamodblocal/data"`: Links the `data` folder on your computer to a folder inside the container. This is how your data gets saved!
        *   The rest of the command tells DynamoDB Local how to behave.
    *   **Keep this terminal window open!** This container needs to keep running for your local database to work.

2.  **Create Your Database Tables:**
    Now that the database is running, we need to create the "tables" inside it where our data will live. We'll use the AWS CLI for this.

    *   Open a **new** terminal window.
    *   **Create the `KidsRewardsUsers` table (or your configured local table name):**
        Refer to your `backend/template.yaml` and `local-env.json` for the exact local table names if they differ from the example. Assuming `local-my-table` for users:
        ```bash
        aws dynamodb create-table \
            --table-name local-my-table \
            --attribute-definitions AttributeName=username,AttributeType=S \
            --key-schema AttributeName=username,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --endpoint-url http://localhost:8000
        ```
    *   **Create the `KidsRewardsStoreItems` table (or your configured local table name):**
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
        *   `--endpoint-url http://localhost:8000` is very important! It tells the AWS CLI to talk to your *local* database, not the real one in the cloud.
        *   If you ever need to start fresh, you can delete these tables with `aws dynamodb delete-table --table-name YourTableName --endpoint-url http://localhost:8000` (e.g., for `KidsRewardsUsers`, `KidsRewardsStoreItems`, `KidsRewardsPurchaseLogs`, `KidsRewardsChores`, `KidsRewardsChoreLogs`) and then run the `create-table` commands again.

3.  **Add Starting Data to Your Tables (Seeding):**
    It's helpful to have some sample users and items in the database when you're developing. We have a script for this.

    *   Make sure you're in the main project directory (`kids_rewards`) in your terminal.
    *   **Set up Python Environment (if you haven't):** It's good practice to use a "virtual environment" for Python projects to keep dependencies separate.
        ```bash
        # Create it (only once)
        python -m venv .venv
        # Activate it (every time you open a new terminal for this project)
        # On macOS/Linux:
        source .venv/bin/activate
        # On Windows:
        # .venv\Scripts\activate
        # Install required packages (only once, or when requirements.txt changes)
        pip install -r backend/requirements.txt
        # Or, if you have uv installed:
        # uv pip install -r backend/requirements.txt
        ```
    *   **Run the Seeding Script:** This command tells Python where to find your project's code (`PYTHONPATH=.`) and which database to talk to. Adjust table names if your local setup uses different ones.
        ```bash
        PYTHONPATH=. DYNAMODB_ENDPOINT_OVERRIDE=http://localhost:8000 USERS_TABLE_NAME=KidsRewardsUsers STORE_ITEMS_TABLE_NAME=KidsRewardsStoreItems PURCHASE_LOGS_TABLE_NAME=KidsRewardsPurchaseLogs CHORES_TABLE_NAME=KidsRewardsChores CHORE_LOGS_TABLE_NAME=KidsRewardsChoreLogs python scripts/seed_dynamodb.py
        ```
        This will add users like "testparent" and "testkid" to your local database. (Note: The seed script may need updating to populate chore tables if desired).

4.  **Prepare and Run the Backend Application (SAM Local):**
    Now we'll run the actual backend code using AWS SAM CLI. Since our Lambda is packaged as a Docker image, SAM CLI will build this image locally.

    *   Open a **new** terminal window (or use the one where you activated the Python virtual environment). Make sure you're in the main `kids_rewards` project directory.
    *   **Build the SAM Application (Optional but good practice):** While `sam local start-api` can build the image, running `sam build` first can sometimes help catch template or configuration issues earlier.
        ```bash
        sam build -t backend/template.yaml
        ```
    *   **Set up Local Environment File:** Your backend needs a special file called `local-env.json` to know how to connect to your local database and other settings. We provide an example file called `local-env.example.json`.
        *   In your project's main folder (`kids_rewards`), make a copy of `local-env.example.json` and name the copy `local-env.json`.
        *   Ensure the table names in `local-env.json` match what you created locally (e.g., `KidsRewardsUsers`, `KidsRewardsStoreItems`, `KidsRewardsPurchaseLogs`, `KidsRewardsChores`, `KidsRewardsChoreLogs`).
    *   **Start the Local API:** This command runs your backend.
        *   It uses your `backend/template.yaml` to understand your function configuration (including the Dockerfile location).
        *   `local-env.json` provides environment variables to the running container.
        *   `--docker-network kidsrewards-network` connects your backend container to the same network as your database.
        ```bash
        sam local start-api -t backend/template.yaml \
            --env-vars local-env.json \
            --docker-network kidsrewards-network \
            --parameter-overrides "AppImageUri=kidsrewardslambdafunction:latest TableNamePrefix=local- LocalDynamoDBEndpoint=http://localhost:8000"
        ```
        SAM CLI will build the Docker image specified in your `backend/Dockerfile` if it hasn't been built yet or if code changes are detected. Your backend API should then be running, usually at `http://127.0.0.1:3000`.
    *   **Keep this terminal window open!** Your backend needs to keep running.

### Setting up the Local Frontend (The User Interface)

The frontend is what you see in your web browser. It's a React application.

1.  **Install Frontend Dependencies:**
    *   Open a **new** terminal window.
    *   Navigate to the `frontend` directory:
        ```bash
        cd frontend
        ```
    *   Install all the necessary code packages for the frontend:
        ```bash
        npm install
        ```
        (You only need to do this once, or if `frontend/package.json` changes.)

2.  **Run the Frontend Development Server:**
    *   In the same terminal (still in the `frontend` directory), start the React app:
        ```bash
        npm start
        ```
    This will usually open the application automatically in your web browser, typically at `http://localhost:3001`. (Note: The backend runs on port 3000, and the frontend on 3001).
    *   **Keep this terminal window open!** The frontend development server needs to keep running.

### You're All Set for Local Development!

Now you should have:
1.  DynamoDB Local (database) running in a Docker container.
2.  Your backend API running via `sam local start-api` (inside a Docker container).
3.  Your frontend React app running via `npm start`.

You can open `http://localhost:3001` in your browser and start using the app!

**Test Login Credentials:**
*   **Parent User:**
    *   Username: `testparent`
    *   Password: `password456`
*   **Kid User:**
    *   Username: `testkid`
    *   Password: `password123`

If you make changes to the backend Python code (inside the `backend` directory), you'll need to stop `sam local start-api` (Ctrl+C) and restart it. SAM will then rebuild your Docker image with the changes.
If you make changes to the frontend React code, `npm start` will usually update your browser automatically.

---

## 🧪 Testing and Linting

This project uses `pytest` for backend testing, React Testing Library and Playwright for frontend testing, and `Ruff` for Python linting and formatting.

### Backend (Python)

1.  **Activate Virtual Environment:**
    Ensure your Python virtual environment is activated:
    ```bash
    # On macOS/Linux:
    source .venv/bin/activate
    # On Windows:
    # .venv\Scripts\activate
    ```

2.  **Install/Update Dependencies:**
    If you haven't already, or if `backend/requirements.txt` has changed:
    ```bash
    cd backend
    pip install -r requirements.txt
    # Or using uv:
    # uv pip install -r requirements.txt
    cd ..
    ```

3.  **Running Ruff (Linting & Formatting):**
    Ruff helps maintain code quality.
    *   **Check for issues:**
        ```bash
        cd backend
        ruff check .
        ```
    *   **Format code:**
        ```bash
        ruff format .
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

4.  **Running Backend Tests (pytest):**
    *   Navigate to the `backend` directory:
        ```bash
        cd backend
        ```
    *   Set the `APP_SECRET_KEY` environment variable for tests. You can set this in your shell, or use a `.env` file with `python-dotenv` if you prefer (not covered here). For a one-time run:
        ```bash
        APP_SECRET_KEY="your_test_secret_key_at_least_32_chars_long" pytest
        ```
        Or, more commonly, export it for your session:
        ```bash
        export APP_SECRET_KEY="your_test_secret_key_at_least_32_chars_long"
        pytest
        ```
        (For Windows Command Prompt: `set APP_SECRET_KEY="your_test_secret_key_at_least_32_chars_long"` then `pytest`)
        (For Windows PowerShell: `$env:APP_SECRET_KEY="your_test_secret_key_at_least_32_chars_long"` then `pytest`)
    *   Pytest will discover and run tests from the `tests` directory. Coverage reports (HTML and XML) will be generated in `backend/htmlcov/` and `backend/coverage.xml` respectively, as configured in `pyproject.toml`. Open `backend/htmlcov/index.html` in a browser to view the HTML report.

### Frontend (React/TypeScript)

1.  **Navigate to Frontend Directory:**
    ```bash
    cd frontend
    ```

2.  **Install/Update Dependencies:**
    If you haven't already, or if `package.json` has changed:
    ```bash
    npm install
    ```

3.  **Running Unit & Integration Tests (React Testing Library):**
    These tests are typically for individual components or small groups of components.
    ```bash
    npm test
    ```
    This will run tests in watch mode. Press `a` to run all tests once.

4.  **Running End-to-End Tests (Playwright):**
    These tests interact with your application in a real browser.
    *   **Ensure your frontend development server is running:**
        In a separate terminal, from the `frontend` directory:
        ```bash
        npm start
        ```
        (Usually runs on `http://localhost:3001`)
    *   **Run Playwright tests:**
        In another terminal, from the `frontend` directory:
        ```bash
        npm run e2e
        ```
    *   **Run Playwright tests with UI mode (for debugging):**
        ```bash
        npm run e2e:ui
        ```
    *   **Show Playwright HTML report:**
        After tests run, an HTML report is generated in `playwright-report/`.
        ```bash
        npm run e2e:report
        ```
        This will open the report in your browser.

### CI/CD Automation

All these tests and linting checks are also configured to run automatically on every push or pull request to `main` or `develop` branches via GitHub Actions. See [`.github/workflows/ci-tests.yml`](./.github/workflows/ci-tests.yml).

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

## Next Steps & Important Notes

*   **Complete AWS Setup:** Ensure the IAM OIDC Role, GitHub Secrets (`AWS_ROLE_TO_ASSUME`, `SAM_S3_BUCKET_NAME`), and ECR repository are correctly set up as described in the "Prerequisites for Production Deployment" section.
*   **SAM S3 Bucket:** The `SAM_S3_BUCKET_NAME` secret should point to an S3 bucket you own, used by `sam deploy` for packaging.
*   **Amplify Configuration:** Double-check your AWS Amplify settings to ensure it's correctly building from the `main` branch and that its environment variables point to the production API Gateway endpoint. The API Gateway endpoint URL can be found in the outputs of your SAM stack after a successful deployment.
*   **Local Table Names:** The local setup instructions for creating DynamoDB tables and seeding use the default names (`KidsRewardsUsers`, `KidsRewardsStoreItems`, `KidsRewardsPurchaseLogs`, `KidsRewardsChores`, `KidsRewardsChoreLogs`). Verify these against your `backend/template.yaml` (Conditions and Mappings for local environment) and `local-env.json` to ensure consistency if you've customized them.