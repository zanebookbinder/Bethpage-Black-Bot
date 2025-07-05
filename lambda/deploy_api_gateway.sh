#!/bin/bash

# ---------- Config Variables ----------
LAMBDA_NAME="bethpage-black-bot"
API_NAME="bethpage-black-bot-api"
STAGE_NAME="prod"
CONFIG_ROUTE_PATH="/config"
RECENT_TIMES_ROUTE_PATH="/getRecentTimes"
REGISTER_ROUTE_PATH="/register"
GET_USER_CONFIG_PATH="/getUserConfig"
UPDATE_USER_CONFIG_PATH="/updateUserConfig"
VALIDATE_ONE_TIME_LINK_PATH="/validateOneTimeLink"
CREATE_ONE_TIME_LINK_PATH="/createOneTimeLink"

ALLOWED_ORIGINS='["http://localhost:3000"]'

# ---------- 1. Get or Create API Gateway ----------
echo "Checking for existing API named '$API_NAME'..."
API_ID=$(aws apigatewayv2 get-apis \
  --query "Items[?Name=='$API_NAME'].ApiId" \
  --output text)

if [ -z "$API_ID" ]; then
  echo "API not found. Creating new API..."
  API_ID=$(aws apigatewayv2 create-api \
    --name "$API_NAME" \
    --protocol-type HTTP \
    --query 'ApiId' \
    --output text)
else
  echo "API already exists. Using existing API ID: $API_ID"
fi

# ---------- 2. Get Lambda ARN ----------
LAMBDA_ARN=$(aws lambda get-function --function-name $LAMBDA_NAME \
  --query 'Configuration.FunctionArn' \
  --output text)
echo "Lambda ARN: $LAMBDA_ARN"

# ---------- 3. Create Integration ----------
echo "Creating integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:apigateway:$(aws configure get region):lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations \
  --payload-format-version 2.0 \
  --query 'IntegrationId' \
  --output text)
echo "Integration ID: $INTEGRATION_ID"

# ---------- 4. Create Routes ----------
echo "Creating routes..."
ROUTES=(
  "GET $CONFIG_ROUTE_PATH"
  "POST $CONFIG_ROUTE_PATH"
  "GET $RECENT_TIMES_ROUTE_PATH"
  "POST $REGISTER_ROUTE_PATH"
  "GET $GET_USER_CONFIG_PATH"
  "POST $UPDATE_USER_CONFIG_PATH"
  "GET $CREATE_ONE_TIME_LINK_PATH"
  "GET $VALIDATE_ONE_TIME_LINK_PATH"
)

for ROUTE_KEY in "${ROUTES[@]}"; do
  echo "Adding route: $ROUTE_KEY"
  aws apigatewayv2 create-route \
    --api-id "$API_ID" \
    --route-key "$ROUTE_KEY" \
    --target integrations/$INTEGRATION_ID 2>/dev/null || echo "Route '$ROUTE_KEY' may already exist, skipping."
done

# ---------- 5. Create Deployment and Stage ----------
echo "Creating deployment and stage..."
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
  --api-id $API_ID \
  --query 'DeploymentId' \
  --output text)

# Check if stage exists
EXISTING_STAGE=$(aws apigatewayv2 get-stage \
  --api-id $API_ID \
  --stage-name $STAGE_NAME \
  --query 'StageName' \
  --output text 2>/dev/null)

if [ "$EXISTING_STAGE" == "$STAGE_NAME" ]; then
  echo "Stage '$STAGE_NAME' already exists. Updating..."
  aws apigatewayv2 update-stage \
    --api-id $API_ID \
    --stage-name $STAGE_NAME \
    --deployment-id $DEPLOYMENT_ID
else
  echo "Creating stage '$STAGE_NAME'..."
  aws apigatewayv2 create-stage \
    --api-id $API_ID \
    --stage-name $STAGE_NAME \
    --deployment-id $DEPLOYMENT_ID
fi

# ---------- 6. Add Permissions to Lambda ----------
echo "Adding permission to Lambda for API Gateway..."
aws lambda add-permission \
  --function-name $LAMBDA_NAME \
  --statement-id apigateway-access-${API_ID} \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$(aws configure get region):$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*/*" \
  2>/dev/null || echo "Lambda permission already exists, skipping."

# ---------- 6.5 Enable CORS ----------
echo "Enabling CORS..."
aws apigatewayv2 update-api \
  --api-id "$API_ID" \
  --cors-configuration AllowOrigins="$ALLOWED_ORIGINS",AllowMethods='["GET","POST","OPTIONS"]',AllowHeaders='["*"]',ExposeHeaders='["*"]',MaxAge=3600 \
  --no-cli-pager

# ---------- 7. Output Final URL ----------
echo "✅ API Gateway route deployed!"
echo "➡️  Invoke URLs:"
echo "   GET  https://$API_ID.execute-api.$(aws configure get region).amazonaws.com/$STAGE_NAME$config_ROUTE_PATH"
echo "   POST https://$API_ID.execute-api.$(aws configure get region).amazonaws.com/$STAGE_NAME$config_ROUTE_PATH"
echo "   GET  https://$API_ID.execute-api.$(aws configure get region).amazonaws.com/$STAGE_NAME$RECENT_TIMES_ROUTE_PATH"
