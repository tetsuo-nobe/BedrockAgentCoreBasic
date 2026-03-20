"""
Policy Engineのテストスクリプト
実行: python test_policy.py
"""

import json
import sys
import requests
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient


def test_refund(gateway_url, bearer_token, amount):
    """返金リクエストをテスト"""
    response = requests.post(
        gateway_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "RefundTarget___process_refund",
                "arguments": {"amount": amount},
            },
        },
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response


def main():
    # 設定ファイル読み込み
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("config.jsonが見つかりません。先にsetup_policy.pyを実行してください。")
        sys.exit(1)

    gateway_url = config["gateway_url"]
    refund_limit = config["refund_limit"]
    print(f"Gateway: {gateway_url}")
    print(f"返金上限: ${refund_limit}\n")

    # アクセストークン取得
    gateway_client = GatewayClient(region_name=config["region"])
    token = gateway_client.get_access_token_for_cognito(config["client_info"])

    # テスト1: $500の返金(許可されるはず)
    print(f"Test 1: $500の返金 (期待値: 許可)")
    print("-" * 40)
    test_refund(gateway_url, token, 500)
    print()

    # テスト2: $2000の返金(拒否されるはず)
    print(f"Test 2: $2000の返金 (期待値: 拒否)")
    print("-" * 40)
    test_refund(gateway_url, token, 2000)


if __name__ == "__main__":
    main()
