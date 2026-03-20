"""リソース削除スクリプト: python cleanup_policy.py"""

from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
from bedrock_agentcore_starter_toolkit.operations.policy.client import PolicyClient
import json
import time


def cleanup():
    with open("config.json", "r") as f:
        config = json.load(f)

    region = config["region"]
    policy_client = PolicyClient(region_name=region)
    gateway_client = GatewayClient(region_name=region)

    # 1. Policyを削除し、完了を待機
    policy_client.delete_policy(
        policy_engine_id=config["policy_engine_id"],
        policy_id=config["policy_id"],
    )
    print("Policy削除の完了を待機中...")
    time.sleep(15)

    # 2. Policy Engineを削除
    policy_client.delete_policy_engine(
        policy_engine_id=config["policy_engine_id"]
    )

    # 3. Gatewayを削除(ターゲットも自動削除される)
    gateway_client.delete_gateway(
        gateway_identifier=config["gateway_id"]
    )
    print("クリーンアップ完了")


if __name__ == "__main__":
    cleanup()
