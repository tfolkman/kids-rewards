# Troubleshooting Guide

## Common Issues and Solutions

### 🔴 Login Fails with 500 Error

**Symptom:** When trying to login, you see `POST http://localhost:3000/token net::ERR_FAILED 500`

**Cause:** The backend Lambda function cannot connect to DynamoDB.

**Solution:**
```bash
# Restart the development environment
just stop
just dev
```

The issue is usually that the DynamoDB endpoint configuration needs to be updated. The `just dev` command handles this automatically.

### 🔴 Port Already in Use

**Symptom:** Error message saying port 3000 or 3001 is already in use.

**Solution:**
```bash
# Check what's using the ports
lsof -i :3000  # Backend port
lsof -i :3001  # Frontend port
lsof -i :8000  # DynamoDB port

# Kill the process using the port
kill -9 <PID>

# Then restart
just dev
```

### 🔴 Docker Container Already Exists

**Symptom:** Error "container name already in use by container..."

**Solution:** The `just dev` command now handles this automatically by checking for existing containers and restarting them. If you still have issues:

```bash
# Check container status
docker ps -a | grep dynamodb

# Start existing container
docker start dynamodb-local

# OR remove and recreate
docker rm dynamodb-local
just dev
```

### 🔴 Frontend Not Loading

**Symptom:** Frontend doesn't start or shows blank page.

**Cause:** Frontend trying to use wrong port or not started properly.

**Solution:**
```bash
# The frontend must run on port 3001 (backend uses 3000)
# Check if it's running
just status

# View the tmux session to see actual errors
tmux attach -t kids-rewards
# Use Ctrl+B then arrow keys to navigate panes
# Use Ctrl+B then D to detach

# Restart everything
just stop
just dev
```

### 🔴 Database Tables Missing

**Symptom:** Errors about tables not existing.

**Solution:**
```bash
# Tables are created automatically by just dev, but if needed:
just db-create-tables

# Verify tables exist
just db-list
```

### 🔴 Services Not Starting

**Symptom:** Services show as not running when checking status.

**Solution:**
```bash
# Check current status
just status

# View all service logs
tmux attach -t kids-rewards

# Check Docker logs
docker logs dynamodb-local

# Full restart
just stop
just dev
```

### 🔴 Test Users Not Working

**Symptom:** Can't login with testkid/testparent credentials.

**Solution:**
```bash
# Verify users exist in database
aws dynamodb scan --table-name KidsRewardsUsers \
  --endpoint-url http://localhost:8000 \
  --output json | jq '.Items[] | .username'

# If missing, you may need to seed the database
# (Check scripts/seed_dynamodb.py if available)
```

## Useful Commands for Debugging

```bash
# Check everything
just health        # Full system health check
just status        # Quick service status

# View logs
tmux attach -t kids-rewards     # See all service outputs
docker logs dynamodb-local       # Database logs
just logs-backend               # Backend logs

# Database operations
just db-list                    # List all tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Clean restart
just stop          # Stop everything
just clean         # Clean build artifacts
just dev           # Start fresh
```

## Environment Details

- **Frontend:** Runs on http://localhost:3001 (React development server)
- **Backend API:** Runs on http://localhost:3000 (SAM Local API Gateway)
- **DynamoDB:** Runs on http://localhost:8000 (Docker container)
- **Network:** All Docker containers use `kidsrewards-network`
- **Config:** Environment variables in `local-env.json`

## Getting Help

If you're still having issues:

1. Check the tmux session for detailed error messages
2. Ensure all prerequisites are installed (Docker, Python 3.12+, Node.js, AWS CLI, SAM CLI)
3. Try a clean restart: `just stop && just clean && just dev`
4. Check the GitHub repository issues for similar problems