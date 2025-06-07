# Bethpage-Black-Bot

A Python-based web scraper built into a Docker image and deployed to AWS Lambda. This service scrapes the Bethpage Black golf course website for open tee times, filters them based on your preferences, and sends email notifications for new available times. It runs automatically every 5 minutes via AWS EventBridge, with state management handled through DynamoDB.

## Features

- Scrapes Bethpage Black tee time availability
- Filters results by preferred dates, times, and number of open spots
- Sends email alerts for newly available tee times
- Stores and compares current tee times in DynamoDB to avoid duplicate notifications
- Serverless deployment via AWS Lambda and Docker
- Scheduled execution every 5 minutes using EventBridge

## Architecture Overview

The system consists of the following components:

- **Dockerized Python App**: The core logic is written in Python and packaged into a Docker image.
- **AWS Lambda**: Hosts and runs the Docker container serverlessly.
- **Amazon EventBridge**: Triggers the Lambda function every 5 minutes.
- **Amazon DynamoDB**: Stores previously seen tee times to avoid duplicate alerts.
- **Email Notification (via AWS SES)**: Sends an email if new tee times are found matching your preferences.
- **AWS Secrets Manager**: Stores Bethpage login information for security, Lambda reads this info before fetching the tee time data

### Data Flow

1. EventBridge triggers the Lambda function every 5 minutes.
2. Lambda scrapes the Bethpage Black website for tee times.
3. Results are filtered according to user-defined date and time preferences.
4. Filtered times are compared with DynamoDB table and results are saved to the table.
5. If new matches are found, an email is sent to the configured recipient.

## Prerequisites

- AWS CLI configured
- AWS account with permissions to use Lambda, EventBridge, DynamoDB, and SES (or another email service)
- Docker installed locally

## Deployment (can be done via code or cli commands)

1. **Setup**: Create lambda function, EventBridge notifications, DynamoDB table, and IAM roles (see below)
2. `./deploy.sh` script handles docker build, deployment to AWS ECR, and updating the lambda code
3. **Configuration**: Set your date and time preferences  in the environment variables used by the Lambda function.
```
aws lambda update-function-configuration \
  --function-name bethpage-black-bot \
  --environment "Variables={
      "PLAYABLE_DAYS_OF_WEEK": "Saturday;Sunday",
      "MIN_PLAYERS": "2",
      "INCLUDE_HOLIDAYS": "True",
      "EARLIEST_PLAYABLE_TIME": "8:00am",
      "MINIMUM_MINUTES_BEFORE_SUNSET": "320",
      "EXTRA_PLAYABLE_DAYS": "6/19/2025;7/3/2025;7/4/2025;8/29/2025;9/1/2025"
  }"
```
4. **Bethpage Account info setup**: Add email and password for Bethpage account to Amazon Secrets Manager
```
$BETHPAGE_EMAIL = "myfake_email@gmail.com"
$BETHPAGE_PASSWORD = "ilovegolf18"
aws secretsmanager create-secret \
  --name bethpage-secret \
  --description "Credentials for Bethpage Black Bot" \
  --secret-string "{  
\"bethpage_email\":\"$BETHPAGE_EMAIL\",\"bethpage_password\":\"$BETHPAGE_PASSWORD\"
    }"
```



***Infrastructure Setup Via Code (Example, not working)***

1. Create IAM role for Lambda:
```
aws iam create-policy \
  --policy-name bethpage-black-bot-lambda-role \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "VisualEditor0",
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue",
          "ses:*",
          "dynamodb:DeleteItem",
          "dynamodb:GetItem",
          "dynamodb:*",
          "dynamodb:Scan",
          "dynamodb:Query"
        ],
        "Resource": "*"
      }
    ]
  }'
```

2. Create Lambda function
```
aws lambda create-function \
  --function-name Bethpage-Black-Bot \
  --package-type Image \
  --code ImageUri=<your-ecr-image-uri> \
  --role <your-lambda-execution-role-arn>
```

3. Create DynamoDB Table
```
aws dynamodb create-table \
  --table-name bethpage-black-bot \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```
4. Set Up EventBridge Trigger (this cron expression will notify every 5 minutes, can easily be changed to certain times of day or days of the week)
```
aws events put-rule \
  --schedule-expression "cron(0/5 * ? * * *)" \
  --name bethpage-black-bot-scheduler

$LAMBDA_FUNCTION_ARN=(aws lambda get-function --function-name bethpage-black-bot --query 'Configuration.FunctionArn' --output text)

aws events put-targets \
  --rule bethpage-black-bot-scheduler \
  --targets "Id"="1","Arn"="$LAMBDA_FUNCTION_ARN"

aws lambda add-permission \
  --function-name bethpage-black-bot \
  --statement-id eventbridge-trigger \
  --action 'lambda:InvokeFunction' \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:$AWS_ACCOUNT_ID:rule/bethpage-black-bot-scheduler
```

5. Attach IAM policy to Lambda role
```
LAMBDA_ROLE_ARN=$(aws lambda get-function-configuration \
  --function-name bethpage-black-bot \
  --query 'Role' \
  --output text)

ROLE_NAME=$(basename "$LAMBDA_ROLE_ARN")
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/bethpage-black-bot-lambda-role
```

License
MIT License

This project is not affiliated with Bethpage State Park or its operators.

