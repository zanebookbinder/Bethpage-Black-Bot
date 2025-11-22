#!/bin/bash

set -e

LAMBDA_NAME="late-night-show-bot"
IMAGE_NAME="late-night-docker-image"
IMAGE_TAG="v1.0.0"
LAMBDA_TIMEOUT_SECONDS=300
MEMORY_SIZE_MB=512
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
AWS_REGION="us-east-1"
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG"
IAM_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/service-role/bethpaige-black-bot-role-np1ssf1j"

cd $(dirname $0)

echo "🔧 Building Docker image..."
docker build --platform linux/amd64 --provenance=false -t $IMAGE_NAME .

echo "🏷️ Tagging image with: $ECR_URI"
docker tag $IMAGE_NAME:latest $ECR_URI

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "📦 Pushing image to ECR..."
# Ensure ECR repository exists
if ! aws ecr describe-repositories --repository-names "$IMAGE_NAME" --region $AWS_REGION >/dev/null 2>&1; then
  echo "🆕 ECR repository '$IMAGE_NAME' does not exist. Creating it..."
  aws ecr create-repository --repository-name "$IMAGE_NAME" --region $AWS_REGION
  echo "✅ ECR repository '$IMAGE_NAME' created."
fi

docker push $ECR_URI

echo "✅ Docker image successfully pushed to ECR: $ECR_URI"

echo "🚀 Updating Lambda function '$LAMBDA_NAME' with new image..."

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
    
    echo "♻️ Lambda exists. Updating with new image..."
    aws lambda update-function-code \
      --function-name "$LAMBDA_NAME" \
      --image-uri "$ECR_URI" \
      --region $AWS_REGION \
      --no-cli-pager
    echo "✅ Lambda function updated successfully."
else
    echo "🆕 Lambda does not exist. Creating new function..."
    aws lambda create-function \
      --function-name "$LAMBDA_NAME" \
      --package-type Image \
      --code ImageUri="$ECR_URI" \
      --role "$IAM_ROLE_ARN" \
      --region $AWS_REGION \
      --timeout $LAMBDA_TIMEOUT_SECONDS \
      --memory-size $MEMORY_SIZE_MB \
      --no-cli-pager
    echo "✅ Lambda function created successfully."
fi

# Add EventBridge rule to trigger Lambda at 7pm EST daily
RULE_NAME="late-night-show-bot-schedule"
SCHEDULE_EXPRESSION="cron(0 0 * * ? *)" # 7pm EST is 0am UTC

if ! aws events describe-rule --name "$RULE_NAME" --region $AWS_REGION >/dev/null 2>&1; then
  echo "🕒 Creating EventBridge rule for scheduled Lambda triggers at 7pm EST..."
else
  echo "🔄 EventBridge rule already exists, updating..."
fi

aws events put-rule \
--name "$RULE_NAME" \
--schedule-expression "$SCHEDULE_EXPRESSION" \
--region $AWS_REGION \
--no-cli-pager

# Add Lambda as target to the rule
aws events put-targets \
  --rule "$RULE_NAME" \
  --targets "Id=1,Arn=arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:$LAMBDA_NAME" \
  --region $AWS_REGION \
  --no-cli-pager

# Add permission for EventBridge to invoke the Lambda if not already present
PERMISSION_EXISTS=$(aws lambda get-policy --function-name "$LAMBDA_NAME" --region $AWS_REGION --no-cli-pager 2>/dev/null | grep "$RULE_NAME-permission" || true)
if [ -z "$PERMISSION_EXISTS" ]; then
  aws lambda add-permission \
    --function-name "$LAMBDA_NAME" \
    --statement-id "$RULE_NAME-permission" \
    --action "lambda:InvokeFunction" \
    --principal events.amazonaws.com \
    --source-arn "arn:aws:events:$AWS_REGION:$AWS_ACCOUNT_ID:rule/$RULE_NAME" \
    --region $AWS_REGION \
    --no-cli-pager
else
  echo "🔄 Lambda permission for EventBridge already exists."
fi