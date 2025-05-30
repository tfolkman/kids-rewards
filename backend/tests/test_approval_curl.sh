#!/bin/bash

# Test script for chore approval endpoint

echo "Testing Chore Approval Endpoint"
echo "=============================="

# Set variables
API_URL="http://localhost:3000"
CHORE_LOG_ID="838515cb-5782-482f-9d1f-b5067a89c4da"  # From the error message

# First, let's login as a parent to get a token
echo -e "\n1. Logging in as parent..."
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

# Test the approval endpoint
echo -e "\n2. Testing approval endpoint..."
APPROVE_RESPONSE=$(curl -v -X PUT "${API_URL}/chores/logs/${CHORE_LOG_ID}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" 2>&1)

echo -e "\nApproval response:"
echo "$APPROVE_RESPONSE"

# Also let's check if the chore log exists
echo -e "\n3. Getting family chore logs to see if this log exists..."
LOGS_RESPONSE=$(curl -s -X GET "${API_URL}/chores/logs/family/" \
  -H "Authorization: Bearer $TOKEN")

echo "Family chore logs:"
echo "$LOGS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGS_RESPONSE"