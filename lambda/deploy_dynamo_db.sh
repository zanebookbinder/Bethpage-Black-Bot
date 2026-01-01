#!/bin/bash

# Exit on error
set -e

# ---------- Config Variables ----------
AWS_REGION=$(aws configure get region)
CONFIG_TABLE_NAME="bethpage-black-bot-config"
LINKS_TABLE_NAME="bethpage-black-bot-one-time-links"
DAILY_UPDATES_TABLE_NAME="daily-updates-data"

create_table_if_not_exists() {
  local TABLE_NAME=$1

  echo "🔍 Checking if table '$TABLE_NAME' exists..."
  if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$AWS_REGION" --no-cli-pager > /dev/null 2>&1; then
    echo "✅ Table '$TABLE_NAME' already exists. Skipping creation."
  else
    echo "📦 Creating DynamoDB table: $TABLE_NAME"
    aws dynamodb create-table \
      --table-name "$TABLE_NAME" \
      --attribute-definitions AttributeName=id,AttributeType=S \
      --key-schema AttributeName=id,KeyType=HASH \
      --billing-mode PAY_PER_REQUEST \
      --region "$AWS_REGION" \
      --no-cli-pager
    echo "✅ Table created: $TABLE_NAME"
  fi
}

# ---------- Run ----------
create_table_if_not_exists "$CONFIG_TABLE_NAME"
create_table_if_not_exists "$LINKS_TABLE_NAME"
create_table_if_not_exists "$DAILY_UPDATES_TABLE_NAME"
