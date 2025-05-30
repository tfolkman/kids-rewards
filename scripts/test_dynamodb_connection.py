#!/usr/bin/env python3
"""Test DynamoDB connection"""
import os
import boto3

# Set dummy credentials for local DynamoDB
os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"

endpoint = os.getenv("DYNAMODB_ENDPOINT_OVERRIDE", "http://localhost:8000")
print(f"Testing connection to DynamoDB at: {endpoint}")

try:
    dynamodb = boto3.client("dynamodb", endpoint_url=endpoint, region_name="us-west-2")
    response = dynamodb.list_tables()
    print(f"✓ Connected successfully!")
    print(f"Existing tables: {response.get('TableNames', [])}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check if DynamoDB container is running: docker ps | grep dynamodb")
    print("2. Check if port 8000 is accessible: curl http://localhost:8000")
    print("3. If using Docker network, you may need to use container name instead of localhost")