#!/bin/bash
BUCKET_NAME=bethpage-black-bot-ui

# 1. Create bucket
aws s3 mb s3://$BUCKET_NAME

# 2. Enable static hosting
aws s3 website s3://$BUCKET_NAME/ --index-document index.html

# 3. Upload files
aws s3 cp index.html s3://$BUCKET_NAME/
aws s3 cp config.json s3://$BUCKET_NAME/

# 4. Make it public (or use CloudFront signed URLs for private access)
# aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy "{
#   \"Version\": \"2012-10-17\",
#   \"Statement\": [
#     {
#       \"Sid\": \"PublicReadGetObject\",
#       \"Effect\": \"Allow\",
#       \"Principal\": \"*\",
#       \"Action\": \"s3:GetObject\",
#       \"Resource\": \"arn:aws:s3:::$BUCKET_NAME/*\"
#     }
#   ]
# }"

echo "Site deployed at:"
echo "http://$BUCKET_NAME.s3-website-$(aws configure get region).amazonaws.com"

SIGNED_URL=$(aws s3 presign s3://$BUCKET_NAME/index.html --expires-in 3600)
echo "✅ Site uploaded securely."
echo "🔐 Temporary signed URL (valid 1 hour):"
echo "$SIGNED_URL"
