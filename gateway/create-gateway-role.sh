#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# AgentCore Gateway 実行ロール作成スクリプト
#   ロール名: myAmazonBedrockAgentCoreGatewayDefaultServiceRole
#   - 信頼ポリシー: bedrock-agentcore.amazonaws.com が引き受け可能
#   - 権限: ターゲット Lambda の呼び出し + GetGateway
# ============================================================

# ===== 設定 =====
ROLE_NAME="myAmazonBedrockAgentCoreGatewayDefaultServiceRole"
REGION="us-west-2"
# 呼び出しを許可する Lambda。まずは全 Lambda を許可（後述の注意参照）。
# 特定関数に絞る場合は下の LAMBDA_ARN を実際の ARN に置き換える。
LAMBDA_ARN="*"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

# ===== 信頼ポリシー（誰がこのロールを引き受けられるか） =====
# 混乱した代理人問題対策として SourceAccount / SourceArn 条件を付与
TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "bedrock-agentcore.amazonaws.com" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "aws:SourceAccount": "${ACCOUNT_ID}" },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:*"
        }
      }
    }
  ]
}
EOF
)

# ===== 権限ポリシー（このロールで何ができるか） =====
PERMISSION_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeLambdaTargets",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "${LAMBDA_ARN}"
    },
    {
      "Sid": "GetGateway",
      "Effect": "Allow",
      "Action": "bedrock-agentcore:GetGateway",
      "Resource": "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:gateway/*"
    }
  ]
}
EOF
)

# ===== ロール作成 =====
aws iam create-role \
  --role-name "${ROLE_NAME}" \
  --assume-role-policy-document "${TRUST_POLICY}" \
  --description "Default service role for Amazon Bedrock AgentCore Gateway"

# ===== インラインポリシーを付与 =====
aws iam put-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-name "AgentCoreGatewayInvokeLambda" \
  --policy-document "${PERMISSION_POLICY}"

echo "作成完了: arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
