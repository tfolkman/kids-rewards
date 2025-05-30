#!/bin/bash

# Final test of the approval fix

echo "Testing Fixed Chore Approval"
echo "============================"

API_URL="http://localhost:3000"
CHORE_LOG_ID="test-log-pending-002"

# Login
echo "1. Logging in..."
TOKEN=$(curl -s -X POST "${API_URL}/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testparent&password=password456" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "   Got token: ${TOKEN:0:20}..."

# Check testkid's current points
echo -e "\n2. Checking testkid's current points..."
curl -s -X GET "${API_URL}/users/" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -m json.tool | grep -A3 -B3 "testkid" | grep -E "(username|points)"

# Test approval
echo -e "\n3. Approving chore log ${CHORE_LOG_ID}..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X PUT "${API_URL}/chores/logs/${CHORE_LOG_ID}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "   HTTP Status: $HTTP_STATUS"
echo "   Response body:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

# Check testkid's points after approval
echo -e "\n4. Checking testkid's points after approval..."
curl -s -X GET "${API_URL}/users/" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -m json.tool | grep -A3 -B3 "testkid" | grep -E "(username|points)"

# Verify the chore log status
echo -e "\n5. Verifying chore log status..."
curl -s -X GET "${API_URL}/chores/logs/family/" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -m json.tool | grep -A10 "$CHORE_LOG_ID" | grep -E "(status|points_value|reviewed_by)"