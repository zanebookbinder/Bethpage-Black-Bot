#!/bin/bash
set -e

APP_NAME="bethpage-black-bot-frontend"
BRANCH_NAME="main"
BUILD_DIR="build"

echo "Building React app..."
npm install
npm run build

echo "Checking for existing Amplify app..."
APP_ID=$(aws amplify list-apps \
  --query "apps[?name=='$APP_NAME'].appId" \
  --output text)

if [ -z "$APP_ID" ]; then
  echo "App not found. Creating new Amplify app: $APP_NAME"
  APP_ID=$(aws amplify create-app \
    --name "$APP_NAME" \
    --query "app.appId" \
    --output text)

  echo "Creating branch: $BRANCH_NAME"
  aws amplify create-branch \
    --app-id "$APP_ID" \
    --branch-name "$BRANCH_NAME" \
	--no-cli-pager
else
  echo "App exists with ID: $APP_ID"
fi

echo "Zipping build output..."
zip -r app.zip $BUILD_DIR

echo "Deploying to Amplify..."
DEPLOY_ID=$(aws amplify start-deployment \
  --app-id "$APP_ID" \
  --branch-name "$BRANCH_NAME" \
  --source app.zip \
  --query "jobSummary.jobId" \
  --output text)

echo "Deployment started! Job ID: $DEPLOY_ID"
