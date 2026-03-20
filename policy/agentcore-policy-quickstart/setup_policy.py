"""
Gateway + Policy Engineのセットアップスクリプト
実行: python setup_policy.py
"""

from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
from bedrock_agentcore_starter_toolkit.operations.policy.client import PolicyClient
from bedrock_agentcore_starter_toolkit.utils.lambda_utils import create_lambda_function
import boto3
import json
import logging
import time


def setup_policy():
    region = "ap-northeast-1"  # 東京リージョン
    refund_limit = 1000

    # クライアント初期化
    gateway_client = GatewayClient(region_name=region)
    gateway_client.logger.setLevel(logging.INFO)
    policy_client = PolicyClient(region_name=region)
    policy_client.logger.setLevel(logging.INFO)

    # Step 1: OAuth認証サーバー作成
    print("Step 1: OAuth認証サーバーを作成中...")
    cognito_response = gateway_client.create_oauth_authorizer_with_cognito(
        "PolicyGateway"
    )

    # Step 2: Gateway作成
    print("Step 2: Gatewayを作成中...")
    gateway = gateway_client.create_mcp_gateway(
        name=None,
        role_arn=None,
        authorizer_config=cognito_response["authorizer_config"],
        enable_semantic_search=False,
    )
    print(f"Gateway URL: {gateway['gatewayUrl']}")

    gateway_client.fix_iam_permissions(gateway)
    print("IAM権限の反映を待機中(30秒)...")
    time.sleep(30)

    # Step 3: Lambda関数(返金ツール)作成
    print("Step 3: Lambda関数を作成中...")
    refund_lambda_code = """
def lambda_handler(event, context):
    amount = event.get('amount', 0)
    return {
        "status": "success",
        "message": f"Refund of ${amount} processed successfully",
        "amount": amount
    }
"""
    session = boto3.Session(region_name=region)
    lambda_arn = create_lambda_function(
        session=session,
        logger=gateway_client.logger,
        function_name=f"RefundTool-{int(time.time())}",
        lambda_code=refund_lambda_code,
        runtime="python3.13",
        handler="lambda_function.lambda_handler",
        gateway_role_arn=gateway["roleArn"],
        description="Refund tool for policy demo",
    )

    # Lambda関数の準備完了を待機
    print("Lambda関数の準備を待機中(10秒)...")
    time.sleep(10)

    # Step 4: Lambdaターゲット追加
    print("Step 4: Lambdaターゲットを追加中...")
    gateway_client.create_mcp_gateway_target(
        gateway=gateway,
        name="RefundTarget",
        target_type="lambda",
        target_payload={
            "lambdaArn": lambda_arn,
            "toolSchema": {
                "inlinePayload": [
                    {
                        "name": "process_refund",
                        "description": "Process a customer refund",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "amount": {
                                    "type": "integer",
                                    "description": "Refund amount in dollars",
                                }
                            },
                            "required": ["amount"],
                        },
                    }
                ]
            },
        },
        credentials=None,
    )

    # Step 5: Policy Engine作成
    print("Step 5: Policy Engineを作成中...")
    engine = policy_client.create_or_get_policy_engine(
        name="RefundPolicyEngine",
        description="Policy engine for refund governance",
    )
    print(f"Policy Engine ID: {engine['policyEngineId']}")

    # Step 6: Cedarポリシー作成
    print(f"Step 6: Cedarポリシーを作成中(返金上限: ${refund_limit})...")
    cedar_statement = (
        f"permit(principal, "
        f'action == AgentCore::Action::"RefundTarget___process_refund", '
        f'resource == AgentCore::Gateway::"{gateway["gatewayArn"]}") '
        f"when {{ context.input.amount < {refund_limit} }};"
    )
    policy = policy_client.create_or_get_policy(
        policy_engine_id=engine["policyEngineId"],
        name="refund_limit_policy",
        description=f"Allow refunds under ${refund_limit}",
        definition={"cedar": {"statement": cedar_statement}},
    )
    print(f"Policy ID: {policy['policyId']}")

    # Step 7: Policy EngineをGatewayにアタッチ(ENFORCEモード)
    print("Step 7: Policy EngineをGatewayにアタッチ中(ENFORCEモード)...")
    gateway_client.update_gateway_policy_engine(
        gateway_identifier=gateway["gatewayId"],
        policy_engine_arn=engine["policyEngineArn"],
        mode="ENFORCE",
    )

    # 設定情報を保存
    config = {
        "gateway_url": gateway["gatewayUrl"],
        "gateway_id": gateway["gatewayId"],
        "gateway_arn": gateway["gatewayArn"],
        "policy_engine_id": engine["policyEngineId"],
        "policy_engine_arn": engine["policyEngineArn"],
        "policy_id": policy["policyId"],
        "region": region,
        "client_info": cognito_response["client_info"],
        "refund_limit": refund_limit,
    }
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("=" * 50)
    print("セットアップ完了!")
    print(f"Gateway URL: {gateway['gatewayUrl']}")
    print(f"返金上限: ${refund_limit}")
    print("設定ファイル: config.json")
    print("次のステップ: python test_policy.py")
    print("=" * 50)
    return config


if __name__ == "__main__":
    setup_policy()
