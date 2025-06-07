#!/bin/bash

# Exit immediately on error
set -e

# Configurable variables
LAMBDA_NAME="bethpage-black-bot"
IMAGE_NAME="docker-images"
IMAGE_TAG="v5.0.0"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
AWS_REGION="us-east-1"
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG"
IAM_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/service-role/bethpaige-black-bot-role-np1ssf1j"

echo "🔧 Building Docker image..."
docker build --platform linux/amd64 --provenance=false -t $IMAGE_NAME .

echo "🏷️ Tagging image with: $ECR_URI"
docker tag $IMAGE_NAME:latest $ECR_URI

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "📦 Pushing image to ECR..."
docker push $ECR_URI

echo "✅ Docker image successfully pushed to ECR: $ECR_URI"

echo "🚀 Updating Lambda function 'bethpage-black-bot' with new image..."

# -------- Create or Update Lambda --------
echo "🔍 Checking if Lambda '$LAMBDA_NAME' exists..."
if aws lambda get-function --function-name "$LAMBDA_NAME" --region $AWS_REGION >/dev/null 2>&1; then
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
      --no-cli-pager
    echo "✅ Lambda function created successfully."
fi