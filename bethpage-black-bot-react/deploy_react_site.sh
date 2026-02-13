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

echo "Creating deployment for Amplify..."
# Get pre-signed URL for upload
DEPLOYMENT_RESPONSE=$(aws amplify create-deployment \
  --app-id "$APP_ID" \
  --branch-name "$BRANCH_NAME" \
  --output json)

ZIP_UPLOAD_URL=$(echo "$DEPLOYMENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['zipUploadUrl'])")
JOB_ID=$(echo "$DEPLOYMENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['jobId'])")

echo "Uploading build to Amplify..."
curl -X PUT -H "Content-Type: application/zip" \
  -T app.zip \
  "$ZIP_UPLOAD_URL"

echo ""
echo "✅ Deployment started! Job ID: $JOB_ID"
echo "📱 Monitor deployment at: https://console.aws.amazon.com/amplify/home?region=us-east-1#/$APP_ID/$BRANCH_NAME/$JOB_ID"
