## 🔧 Troubleshooting

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Quick Fixes

**Most issues are resolved by restarting:**
```bash
just stop
just dev
```

**Check service status:**
```bash
just status  # Quick status check
just health  # Full health check with versions
```

**View running services:**
```bash
tmux attach -t kids-rewards  # See all outputs
# Ctrl+B then D to detach
```

## 📚 Complete Command Reference

For a full list of available commands:
```bash
just --list
```

### Essential Commands:
- **`just dev`** - Start complete development environment with one command
- **`just stop`** - Stop all development services  
- **`just status`** - Check if services are running
- **`just test`** - Run all tests
- **`just format`** - Format and lint code

## Key Improvements

This project now features a streamlined development setup:

✅ **Single Command Setup:** `just dev` handles everything automatically  
✅ **Smart Container Management:** Handles existing Docker containers gracefully  
✅ **Auto-reload Enabled:** Both frontend and backend reload on code changes  
✅ **Automatic Table Creation:** All DynamoDB tables created automatically  
✅ **Port Management:** Frontend on 3001, Backend on 3000 (no conflicts)  
✅ **Better Error Recovery:** Improved handling of common issues  
✅ **Tmux Integration:** Better terminal management for multiple services  

## Next Steps & Important Notes

*   **Complete AWS Setup:** Ensure the IAM OIDC Role, GitHub Secrets (`AWS_ROLE_TO_ASSUME`, `SAM_S3_BUCKET_NAME`), and ECR repository are correctly set up as described in the "Prerequisites for Production Deployment" section.
*   **SAM S3 Bucket:** The `SAM_S3_BUCKET_NAME` secret should point to an S3 bucket you own, used by `sam deploy` for packaging.
*   **Amplify Configuration:** Double-check your AWS Amplify settings to ensure it's correctly building from the `main` branch and that its environment variables point to the production API Gateway endpoint.
*   **Local Development:** The new `just dev` command simplifies local development significantly - use it as your primary way to start the development environment.