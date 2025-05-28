#!/bin/bash

# Exit immediately on error
set -e

# Configurable variables
IMAGE_NAME="docker-images"
IMAGE_TAG="v4.0.0"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
AWS_REGION="us-east-1"
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG"

echo "🔧 Building Docker image..."
docker build --platform linux/amd64 --provenance=false -t $IMAGE_NAME .


echo "🏷️ Tagging image with: $ECR_URI"
docker tag $IMAGE_NAME:latest $ECR_URI

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "📦 Pushing image to ECR..."
docker push $ECR_URI

echo "✅ Docker image successfully pushed to ECR: $ECR_URI"

echo "🚀 Updating Lambda function 'bethpaige-black-bot' with new image..."

aws lambda update-function-code \
  --function-name bethpaige-black-bot \
  --image-uri $ECR_URI

echo "✅ Lambda function updated successfully."