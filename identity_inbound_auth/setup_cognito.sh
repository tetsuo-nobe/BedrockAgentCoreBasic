#!/bin/bash

# 使い方: ./setup_cognito.sh [リージョン名]
# リージョン名を省略した場合は us-west-2 を使用する
REGION="${1:-us-west-2}"

echo "使用するリージョン: ${REGION}"

# Create User Pool and capture Pool ID directly
export POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name "MyUserPool" \
  --policies '{"PasswordPolicy":{"MinimumLength":8}}' \
  --region "${REGION}" | jq -r '.UserPool.Id')

# Create App Client and capture Client ID directly
export CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $POOL_ID \
  --client-name "MyClient" \
  --no-generate-secret \
  --explicit-auth-flows "ALLOW_USER_PASSWORD_AUTH" "ALLOW_REFRESH_TOKEN_AUTH" \
  --region "${REGION}" | jq -r '.UserPoolClient.ClientId')

# Create User
aws cognito-idp admin-create-user \
  --user-pool-id $POOL_ID \
  --username "testuser" \
  --temporary-password "TEMP_PASSWORD" \
  --region "${REGION}" \
  --message-action SUPPRESS > /dev/null

# Set Permanent Password
aws cognito-idp admin-set-user-password \
  --user-pool-id $POOL_ID \
  --username "testuser" \
  --password "PERMANENT_PASSWORD" \
  --region "${REGION}" \
  --permanent > /dev/null

# Authenticate User and capture Access Token
export BEARER_TOKEN=$(aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME='testuser',PASSWORD='PERMANENT_PASSWORD' \
  --region "${REGION}" | jq -r '.AuthenticationResult.AccessToken')

export DISCOVERY_URL=https://cognito-idp.${REGION}.amazonaws.com/$POOL_ID/.well-known/openid-configuration

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
