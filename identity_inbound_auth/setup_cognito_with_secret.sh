#!/bin/bash

# 環境変数を設定
export USERNAME="testuser"
export PASSWORD="PERMANENT_PASSWORD"
export REGION="us-east-1"

# Create User Pool and capture Pool ID directly
export POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name "test0224Pool" \
  --policies '{"PasswordPolicy":{"MinimumLength":8}}' \
  --region us-east-1 | jq -r '.UserPool.Id')

# クライアントシークレットありで作成
CLIENT_RESPONSE=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $POOL_ID \
  --client-name "test0224ClientWithSecret" \
  --generate-secret \
  --explicit-auth-flows "ALLOW_USER_PASSWORD_AUTH" "ALLOW_REFRESH_TOKEN_AUTH" \
  --region $REGION \
  --query 'UserPoolClient.{ClientId:ClientId,ClientSecret:ClientSecret}' \
  --output json)

export CLIENT_ID=$(echo $CLIENT_RESPONSE | jq -r '.ClientId')
export CLIENT_SECRET=$(echo $CLIENT_RESPONSE | jq -r '.ClientSecret')
export DISCOVERY_URL="https://cognito-idp.us-east-1.amazonaws.com/$POOL_ID/.well-known/openid-configuration"

# Create User
aws cognito-idp admin-create-user \
  --user-pool-id $POOL_ID \
  --username "${USERNAME}" \
  --temporary-password "${PASSWORD}" \
  --region $REGION \
  --message-action SUPPRESS > /dev/null

# Set Permanent Password
aws cognito-idp admin-set-user-password \
  --user-pool-id $POOL_ID \
  --username "testuser" \
  --password "PERMANENT_PASSWORD" \
  --region $REGION \
  --permanent > /dev/null

# SECRET_HASHを計算
export SECRET_HASH=$(python3 -c "
import hmac
import hashlib
import base64
message = '${USERNAME}${CLIENT_ID}'
secret = '${CLIENT_SECRET}'
dig = hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
print(base64.b64encode(dig).decode())
")

# トークンを取得
export BEARER_TOKEN=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="${USERNAME}",PASSWORD="${PASSWORD}",SECRET_HASH="${SECRET_HASH}" \
  --region "$REGION" | jq -r '.AuthenticationResult.AccessToken')

echo "Access Token: $BEARER_TOKEN"


# Output the required values
echo "Pool id: $POOL_ID"
echo "Discovery URL: $DISCOVERY_URL"
echo "Client ID: $CLIENT_ID"
echo "Bearer Token: $BEARER_TOKEN"

# Save to .env file for later use
cat > cognito.env << EOF
export POOL_ID="$POOL_ID"
export DISCOVERY_URL="$DISCOVERY_URL"
export CLIENT_ID="$CLIENT_ID"
export BEARER_TOKEN="$BEARER_TOKEN"
EOF

echo ""
echo "Environment variables saved to cognito.env"
echo "To use them, run: source cognito.env"
