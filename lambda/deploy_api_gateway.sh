#!/bin/bash

# ---------- Config Variables ----------
LAMBDA_NAME="bethpaige-black-bot"          # Your Lambda function name
API_NAME="bethpage-black-bot-api"
STAGE_NAME="prod"
CONFIG_ROUTE_PATH="/config"
RECENT_TIMES_ROUTE_PATH="/getRecentTimes"

# ---------- 1. Create API Gateway HTTP API ----------
echo "Creating API..."
API_ID=$(aws apigatewayv2 create-api \
  --name "$API_NAME" \
  --protocol-type HTTP \
  --query 'ApiId' \
  --output text)

echo "API ID: $API_ID"

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

# CONFIG GET/POST ROUTES
echo "Creating routes..."
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "GET $CONFIG_ROUTE_PATH" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST $CONFIG_ROUTE_PATH" \
  --target integrations/$INTEGRATION_ID

# GET RECENT TIMES ROUTE
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "GET $RECENT_TIMES_ROUTE_PATH" \
  --target integrations/$INTEGRATION_ID

# ---------- 5. Create Stage ----------
echo "Creating deployment and stage..."
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
  --api-id $API_ID \
  --query 'DeploymentId' \
  --output text)

aws apigatewayv2 create-stage \
  --api-id $API_ID \
  --stage-name $STAGE_NAME \
  --deployment-id $DEPLOYMENT_ID

# ---------- 6. Add Permissions to Lambda ----------
echo "Adding permission to Lambda for API Gateway..."
aws lambda add-permission \
  --function-name $LAMBDA_NAME \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$(aws configure get region):$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*/*"

# ---------- 7. Output Final URL ----------
echo "✅ API Gateway route deployed!"
echo "➡️  Invoke URLs:"
echo "   GET  https://$API_ID.execute-api.$(aws configure get region).amazonaws.com/$STAGE_NAME/config"
echo "   POST https://$API_ID.execute-api.$(aws configure get region).amazonaws.com/$STAGE_NAME/config"
echo "   GET  https://$API_ID.execute-api.$(aws configure get region).amazonaws.com/$STAGE_NAME/recent-times"