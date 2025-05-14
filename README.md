# Kids Rewards Project

Welcome to the Kids Rewards project! This guide will help you understand how to set up and work with the project in different environments: local development, staging, and production.

## 🚀 Getting Started: Local Development

This section explains how to run the backend (the "brain" of the app) and the frontend (what you see and interact with in the browser) on your own computer. This is great for making changes and testing things out!

### What You'll Need (Prerequisites)

Before you start, make sure you have these tools installed on your machine:

*   **Docker Desktop:** We use this to run a local version of our database (DynamoDB). Think of it as a mini-server for our data that runs on your computer.
*   **Python:** The backend is written in Python (we're using version 3.12).
*   **pip:** Python's package installer (usually comes with Python).
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
    *   **Create the `KidsRewardsUsers` table:**
        ```bash
        aws dynamodb create-table \
            --table-name KidsRewardsUsers \
            --attribute-definitions AttributeName=username,AttributeType=S \
            --key-schema AttributeName=username,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --endpoint-url http://localhost:8000
        ```
    *   **Create the `KidsRewardsStoreItems` table:**
        ```bash
        aws dynamodb create-table \
            --table-name KidsRewardsStoreItems \
            --attribute-definitions AttributeName=id,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --endpoint-url http://localhost:8000
        ```
        *   `--endpoint-url http://localhost:8000` is very important! It tells the AWS CLI to talk to your *local* database, not the real one in the cloud.
        *   If you ever need to start fresh, you can delete these tables with `aws dynamodb delete-table --table-name KidsRewardsUsers --endpoint-url http://localhost:8000` (and similarly for `KidsRewardsStoreItems`) and then run the `create-table` commands again.

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
        ```
    *   **Run the Seeding Script:** This command tells Python where to find your project's code (`PYTHONPATH=.`) and which database to talk to.
        ```bash
        PYTHONPATH=. DYNAMODB_ENDPOINT_OVERRIDE=http://localhost:8000 python scripts/seed_dynamodb.py --environment local --users-table KidsRewardsUsers --store-items-table KidsRewardsStoreItems
        ```
        This will add users like "testparent" and "testkid" to your local database.

4.  **Prepare and Run the Backend Application (SAM Local):**
    Now we'll run the actual backend code using AWS SAM CLI.

    *   Open a **new** terminal window (or use the one where you activated the Python virtual environment). Make sure you're in the main `kids_rewards` project directory.
    *   **Build the SAM Application:** This step packages your backend code.
        ```bash
        sam build -t backend/template.yaml
        ```
    *   **Set up Local Environment File:** Your backend needs a special file called `local-env.json` to know how to connect to your local database and other settings. We provide an example file called `local-env.example.json`.
        *   In your project's main folder (`kids_rewards`), make a copy of `local-env.example.json` and name the copy `local-env.json`.
        *   You usually don't need to change anything in `local-env.json` for the default local setup.
    *   **Start the Local API:** This command runs your backend. It uses:
        *   `local-env.json`: The file you just created, which tells your local backend important settings.
        *   `--docker-network kidsrewards-network`: Connects your backend (which also runs in a Docker container via SAM) to the same network as your database.
        ```bash
        sam local start-api -t .aws-sam/build/template.yaml --env-vars local-env.json --docker-network kidsrewards-network
        ```
        Your backend API should now be running, usually at `http://127.0.0.1:3000`.
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
2.  Your backend API running via `sam local start-api`.
3.  Your frontend React app running via `npm start`.

You can open `http://localhost:3001` in your browser and start using the app!

**Test Login Credentials:**
*   **Parent User:**
    *   Username: `testparent`
    *   Password: `password456`
*   **Kid User:**
    *   Username: `testkid`
    *   Password: `password123`

If you make changes to the backend Python code, `sam local start-api` should often pick them up automatically. If not, you might need to stop it (Ctrl+C) and re-run `sam build` and then `sam local start-api`.
If you make changes to the frontend React code, `npm start` will usually update your browser automatically.

---
*(The rest of your README.md for Staging and Production can follow here)*
---

## 🌍 Staging Environment

The staging environment is an isolated environment created automatically for each feature branch. This allows you to test your changes in an environment that is very similar to production before merging your code.

### How it Works

We use **GitHub Actions** and **AWS Amplify** to automate the deployment to staging:

1.  **GitHub Actions Workflow:** When you push code to a branch that starts with `feat/` (e.g., `feat/new-feature`) or open a Pull Request targeting `main` or `develop`, a GitHub Actions workflow (`.github/workflows/staging-deploy.yml`) is triggered.
2.  **Backend Deployment:** This workflow uses AWS SAM CLI to build and deploy your backend code to a new, temporary AWS CloudFormation stack. The stack name and DynamoDB table names are dynamically generated based on your branch name.
3.  **Backend Seeding:** After the backend is deployed, the workflow runs the `scripts/seed_dynamodb.py` script to populate the staging database with test data.
4.  **Frontend Deployment (Amplify Previews):** AWS Amplify is configured to automatically detect new branches and deploy the frontend code for those branches to a unique preview URL.
5.  **Connecting Frontend and Backend:** The Amplify-deployed frontend needs to know the URL of the dynamically deployed staging backend. This requires an additional step in the GitHub Actions workflow to fetch the backend URL after deployment and update an environment variable in the Amplify preview environment. **(Note: This step needs to be fully implemented in the workflow.)**

### Using the Staging Environment

1.  **Create a Feature Branch:** Create a new branch for your work, starting with `feat/` (e.g., `git checkout -b feat/my-awesome-feature`).
2.  **Push Your Changes:** Push your code changes to this branch (`git push origin feat/my-awesome-feature`).
3.  **Monitor the Workflow:** Go to the "Actions" tab in your GitHub repository to see the "Deploy Staging Backend" workflow running.
4.  **Access the Staging Environment:** Once the workflow completes successfully, you will get a unique URL for your staging environment (both frontend and backend API). You can find these URLs in the workflow run logs or potentially in a comment on your Pull Request (if configured).
5.  **Test Your Changes:** Test your new features and changes in this isolated staging environment.
6.  **Teardown:** When you close the Pull Request associated with your feature branch or delete the `feat/` branch, the `.github/workflows/staging-teardown.yml` workflow will automatically run to delete the temporary backend CloudFormation stack, cleaning up the AWS resources.

## 🚀 Production Environment

The production environment is where the live version of the application runs. Deployments to production should be done carefully and typically require approval.

### How it Works

We will use a GitHub Actions workflow (`.github/workflows/prod-deploy.yml`) to automate production deployments:

1.  **Trigger:** This workflow will be triggered when code is merged into the `main` branch (our designated production branch).
2.  **Approval:** Before the deployment to production starts, the workflow will require a manual approval step. This ensures that someone reviews and approves the changes before they go live.
3.  **Backend Deployment:** Once approved, the workflow will build and deploy the backend code to the production AWS environment using AWS SAM CLI. This will update the main CloudFormation stack and associated resources (like the production DynamoDB tables).
4.  **Frontend Deployment:** The production frontend deployment process will depend on how it's hosted (e.g., Amplify, S3/CloudFront). You will need to ensure the production frontend is updated after a successful backend deployment and is configured to point to the production backend API Gateway URL. **(Note: The exact steps for production frontend deployment and connecting it to the backend need to be defined based on your setup.)**

### Deploying to Production

1.  **Merge to Main:** Ensure your feature branch has been thoroughly tested in the staging environment and is ready to go live. Merge your feature branch into the `main` branch.
2.  **Request Approval:** The "Deploy Production Backend" GitHub Actions workflow will start. It will pause and wait for approval.
3.  **Approve Deployment:** A designated approver (e.g., a parent or lead developer) will need to go to the "Actions" tab in GitHub, find the production deployment workflow run, and approve the deployment.
4.  **Monitor Deployment:** Once approved, the workflow will proceed with deploying the backend to production. Monitor the workflow run logs to ensure the deployment is successful.
5.  **Verify Production:** After the workflow completes, verify that the changes are live in the production environment.

## Next Steps

*   Implement the step in `.github/workflows/staging-deploy.yml` to fetch the staging backend API Gateway URL and update the Amplify preview environment variable.
*   Define and implement the production frontend deployment process and how it connects to the production backend.
*   Replace `YOUR_SAM_DEPLOYMENT_BUCKET_NAME` in `.github/workflows/staging-deploy.yml` and `.github/workflows/prod-deploy.yml` with the actual name of your S3 bucket for SAM deployment artifacts.
*   Add AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION) as secrets in your GitHub repository settings.