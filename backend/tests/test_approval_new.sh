#!/bin/bash

# Test script for chore approval endpoint with new test data

echo "Testing Chore Approval with test-log-pending-001"
echo "==============================================="

# Set variables
API_URL="http://localhost:3000"
CHORE_LOG_ID="test-log-pending-001"

# First, let's login as a parent to get a token
echo -e "\n1. Logging in as testparent..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testparent&password=password456")

echo "Login response: $LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Failed to get token!"
  exit 1
fi

echo "Got token: ${TOKEN:0:20}..."

# Get family chore logs to verify our test log is there
echo -e "\n2. Getting family chore logs..."
LOGS_RESPONSE=$(curl -s -X GET "${API_URL}/chores/logs/family/" \
  -H "Authorization: Bearer $TOKEN")

echo "Family chore logs:"
echo "$LOGS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGS_RESPONSE"

# Test the approval endpoint
echo -e "\n3. Testing approval endpoint for test-log-pending-001..."
APPROVE_RESPONSE=$(curl -v -X PUT "${API_URL}/chores/logs/${CHORE_LOG_ID}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" 2>&1)

echo -e "\nApproval response:"
echo "$APPROVE_RESPONSE" | grep -E "(HTTP/|{.*})" || echo "$APPROVE_RESPONSE"

# Check the log status after approval
echo -e "\n4. Checking family logs again to see if status changed..."
LOGS_AFTER=$(curl -s -X GET "${API_URL}/chores/logs/family/" \
  -H "Authorization: Bearer $TOKEN")

echo "Family chore logs after approval:"
echo "$LOGS_AFTER" | python3 -m json.tool | grep -A5 -B5 "test-log-pending-001" || echo "Log not found"