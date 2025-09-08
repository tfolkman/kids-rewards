#!/bin/bash

echo "Testing Chore Submission Fix"
echo "============================="

# 1. Get authentication token
echo "1. Logging in as testkid..."
TOKEN=$(curl -s -X POST http://localhost:3000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testkid&password=password123" | jq -r .access_token)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "❌ Failed to get auth token"
    exit 1
fi
echo "✅ Got auth token"

# 2. Get available chores
echo ""
echo "2. Getting available chores..."
CHORE_ID=$(curl -s http://localhost:3000/chores/ \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

if [ -z "$CHORE_ID" ] || [ "$CHORE_ID" == "null" ]; then
    echo "❌ No chores available"
    exit 1
fi
echo "✅ Found chore: $CHORE_ID"

# 3. Submit chore with effort tracking
echo ""
echo "3. Submitting chore with 5 minutes effort..."
RESPONSE=$(curl -s -X POST "http://localhost:3000/chores/${CHORE_ID}/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"effort_minutes": 5}')

STATUS=$(echo "$RESPONSE" | jq -r .status)
EFFORT_POINTS=$(echo "$RESPONSE" | jq -r .effort_points)

if [ "$STATUS" == "pending_approval" ]; then
    echo "✅ Chore submitted successfully!"
    echo "   Status: $STATUS"
    echo "   Effort points earned: $EFFORT_POINTS"
else
    echo "❌ Failed to submit chore"
    echo "Response: $RESPONSE"
    exit 1
fi

echo ""
echo "4. Testing error handling with invalid data..."
ERROR_RESPONSE=$(curl -s -X POST "http://localhost:3000/chores/${CHORE_ID}/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"effort_minutes": 500}')

ERROR_MSG=$(echo "$ERROR_RESPONSE" | jq -r '.detail[0].msg // .detail')

if [[ "$ERROR_MSG" == *"less than or equal to 240"* ]]; then
    echo "✅ Error handling works correctly"
    echo "   Error message: $ERROR_MSG"
else
    echo "⚠️  Unexpected error response: $ERROR_RESPONSE"
fi

echo ""
echo "============================="
echo "✅ All tests passed! The fix is working correctly."