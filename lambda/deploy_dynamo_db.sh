#!/bin/bash

# Exit on error
set -e

# ---------- Config Variables ----------
DYNAMO_TABLE_NAME="bethpage-black-bot-config"
AWS_REGION=$(aws configure get region)

# ---------- Create DynamoDB Table ----------
echo "📦 Creating DynamoDB table: $DYNAMO_TABLE_NAME"
aws dynamodb create-table \
  --table-name "$DYNAMO_TABLE_NAME" \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$AWS_REGION" \
  --no-cli-pager

echo "✅ DynamoDB table created successfully: $DYNAMO_TABLE_NAME"
