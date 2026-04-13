#!/bin/bash

set -e

# ---------- Config ----------
LAMBDA_NAME="daily-data-input-lambda"
IMAGE_NAME="daily-data-input-docker-image"
IMAGE_TAG="v1.0.0"
LAMBDA_TIMEOUT_SECONDS=30
MEMORY_SIZE_MB=256
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
AWS_REGION="us-east-1"
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG"
IAM_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/service-role/bethpaige-black-bot-role-np1ssf1j"
IAM_ROLE_NAME="bethpaige-black-bot-role-np1ssf1j"
S3_BUCKET="daily-update-bot-data"
API_NAME="daily-data-input-api"
STAGE_NAME="prod"

cd $(dirname $0)

# ---------- 1. S3 Bucket ----------
echo "🪣 Checking for S3 bucket '$S3_BUCKET'..."
if aws s3api head-bucket --bucket "$S3_BUCKET" --region "$AWS_REGION" 2>/dev/null; then
  echo "✅ S3 bucket '$S3_BUCKET' already exists."
else
  echo "🆕 Creating S3 bucket '$S3_BUCKET'..."
  aws s3api create-bucket \
    --bucket "$S3_BUCKET" \
    --region "$AWS_REGION" \
    --no-cli-pager
  echo "✅ S3 bucket created."
fi

# ---------- 2. S3 Permissions for Lambda Role ----------
echo "🔐 Attaching S3 permissions to Lambda role '$IAM_ROLE_NAME'..."
aws iam put-role-policy \
  --role-name "$IAM_ROLE_NAME" \
  --policy-name "daily-update-bot-data-s3-access" \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"s3:GetObject\",
          \"s3:PutObject\",
          \"s3:ListBucket\"
        ],
        \"Resource\": [
          \"arn:aws:s3:::$S3_BUCKET\",
          \"arn:aws:s3:::$S3_BUCKET/*\"
        ]
      }
    ]
  }" \
  --no-cli-pager
echo "✅ S3 permissions attached."

# ---------- 3. Build and Push Docker Image ----------
echo "🔧 Building Docker image..."
docker build --platform linux/amd64 --provenance=false -t $IMAGE_NAME .

echo "🏷️ Tagging image: $ECR_URI"
docker tag $IMAGE_NAME:latest $ECR_URI

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "📦 Pushing image to ECR..."
if ! aws ecr describe-repositories --repository-names "$IMAGE_NAME" --region $AWS_REGION >/dev/null 2>&1; then
  echo "🆕 Creating ECR repository '$IMAGE_NAME'..."
  aws ecr create-repository --repository-name "$IMAGE_NAME" --region $AWS_REGION
fi
docker push $ECR_URI
echo "✅ Image pushed to ECR: $ECR_URI"

# ---------- 4. Create or Update Lambda ----------
echo "🚀 Deploying Lambda '$LAMBDA_NAME'..."
if aws lambda get-function --function-name "$LAMBDA_NAME" --region $AWS_REGION >/dev/null 2>&1; then
  CURRENT_TIMEOUT=$(aws lambda get-function-configuration \
    --function-name "$LAMBDA_NAME" \
    --region $AWS_REGION \
    --query "Timeout" \
    --output text)

  if [ "$CURRENT_TIMEOUT" -ne $LAMBDA_TIMEOUT_SECONDS ]; then
    echo "🛠️ Updating function configuration (timeout = $LAMBDA_TIMEOUT_SECONDS seconds)..."
    aws lambda update-function-configuration \
      --function-name "$LAMBDA_NAME" \
      --timeout $LAMBDA_TIMEOUT_SECONDS \
      --region $AWS_REGION \
      --no-cli-pager
    aws lambda wait function-updated --function-name "$LAMBDA_NAME" --region $AWS_REGION
  fi

  echo "♻️ Lambda exists. Updating image..."
  aws lambda update-function-code \
    --function-name "$LAMBDA_NAME" \
    --image-uri "$ECR_URI" \
    --region $AWS_REGION \
    --no-cli-pager
  echo "✅ Lambda updated."
else
  echo "🆕 Creating Lambda '$LAMBDA_NAME'..."
  aws lambda create-function \
    --function-name "$LAMBDA_NAME" \
    --package-type Image \
    --code ImageUri="$ECR_URI" \
    --role "$IAM_ROLE_ARN" \
    --region $AWS_REGION \
    --timeout $LAMBDA_TIMEOUT_SECONDS \
    --memory-size $MEMORY_SIZE_MB \
    --environment "Variables={DATA_INPUT_API_KEY=REPLACE_ME}" \
    --no-cli-pager
  echo "✅ Lambda created."
  echo "⚠️  Remember to set the DATA_INPUT_API_KEY environment variable on the Lambda."
fi

# ---------- 5. API Gateway ----------
echo "🌐 Setting up API Gateway '$API_NAME'..."
API_ID=$(aws apigatewayv2 get-apis \
  --query "Items[?Name=='$API_NAME'].ApiId" \
  --output text)

if [ -z "$API_ID" ]; then
  echo "🆕 Creating API Gateway..."
  API_ID=$(aws apigatewayv2 create-api \
    --name "$API_NAME" \
    --protocol-type HTTP \
    --query 'ApiId' \
    --output text)
  echo "✅ API created: $API_ID"
else
  echo "✅ API already exists: $API_ID"
fi

LAMBDA_ARN=$(aws lambda get-function \
  --function-name "$LAMBDA_NAME" \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Creating integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --payload-format-version 2.0 \
  --query 'IntegrationId' \
  --output text)

echo "Creating routes..."
aws apigatewayv2 create-route \
  --api-id "$API_ID" \
  --route-key "POST /health-data" \
  --target "integrations/$INTEGRATION_ID" 2>/dev/null || echo "Route 'POST /health-data' may already exist, skipping."

echo "Creating deployment and stage..."
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
  --api-id $API_ID \
  --query 'DeploymentId' \
  --output text)

EXISTING_STAGE=$(aws apigatewayv2 get-stage \
  --api-id $API_ID \
  --stage-name $STAGE_NAME \
  --query 'StageName' \
  --output text 2>/dev/null || echo "")

if [ "$EXISTING_STAGE" == "$STAGE_NAME" ]; then
  echo "🔄 Updating stage '$STAGE_NAME'..."
  aws apigatewayv2 update-stage \
    --api-id $API_ID \
    --stage-name $STAGE_NAME \
    --deployment-id $DEPLOYMENT_ID \
    --no-cli-pager
else
  echo "🆕 Creating stage '$STAGE_NAME'..."
  aws apigatewayv2 create-stage \
    --api-id $API_ID \
    --stage-name $STAGE_NAME \
    --deployment-id $DEPLOYMENT_ID \
    --no-cli-pager
fi

# ---------- 6. Lambda Permission for API Gateway ----------
echo "🔐 Adding Lambda permission for API Gateway..."
aws lambda add-permission \
  --function-name "$LAMBDA_NAME" \
  --statement-id "apigateway-access-${API_ID}" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$AWS_REGION:$AWS_ACCOUNT_ID:$API_ID/*/*/*" \
  --region $AWS_REGION \
  --no-cli-pager 2>/dev/null || echo "Lambda permission already exists, skipping."

# ---------- 7. Output ----------
echo ""
echo "✅ Deployment complete!"
echo "➡️  Endpoint: POST https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/$STAGE_NAME/health-data"
echo "   Header:   x-api-key: <DATA_INPUT_API_KEY>"
