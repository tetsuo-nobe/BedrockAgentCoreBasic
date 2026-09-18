"""AgentCore harness を呼び出すサンプル (AWS SDK for Python / boto3 版)

harness ID / ARN は環境変数 HARNESS_ARN から取得します (harness は事前作成済みが前提)。
参考: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-get-started.html
"""

import os
import sys
import uuid

import boto3

# ------------------------------------------------------------
# 設定値
# ------------------------------------------------------------
# 事前作成済みの AgentCore harness の ARN (環境変数から取得)
HARNESS_ARN = os.environ.get("HARNESS_ARN")

# AWSリージョン (未指定時は us-west-2 を既定値とする)
REGION = os.environ.get("AWS_REGION", "us-west-2")

# 呼び出すエンドポイント名 (未指定時は DEFAULT エンドポイントを使用)
QUALIFIER = os.environ.get("QUALIFIER", "DEFAULT")


def invoke_harness(client, prompt: str, session_id: str) -> str:
    """InvokeHarness を呼び出し、ストリーミングで応答テキストを受け取って返す。"""
    response = client.invoke_harness(
        harnessArn=HARNESS_ARN,
        qualifier=QUALIFIER,
        runtimeSessionId=session_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
    )

    # レスポンスはイベントストリームで返るため、
    # テキストの差分 (contentBlockDelta) を逐次表示しながら連結する
    chunks = []
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            text = delta.get("text")
            if text:
                print(text, end="", flush=True)
                chunks.append(text)
        elif "runtimeClientError" in event:
            raise RuntimeError(f"harness 実行中にエラーが発生しました: {event['runtimeClientError']}")
        elif "internalServerException" in event:
            raise RuntimeError(f"サービス内部エラーが発生しました: {event['internalServerException']}")

    print()  # 最後に改行
    return "".join(chunks)


def main() -> None:
    if not HARNESS_ARN:
        print("エラー: 環境変数 HARNESS_ARN が設定されていません。", file=sys.stderr)
        print(
            '例 (PowerShell): $env:HARNESS_ARN = "arn:aws:bedrock-agentcore:us-west-2:123456789012:harness/MyHarness-XyZ123"',
            file=sys.stderr,
        )
        sys.exit(1)

    # コマンドライン引数があればそれをプロンプトにする。なければ既定値。
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "こんにちは"

    # runtimeSessionId は 33 文字以上である必要がある。
    # 会話を継続したい場合は環境変数 SESSION_ID に前回と同じ値を設定して実行する。
    session_id = os.environ.get("SESSION_ID") or (str(uuid.uuid4()) + str(uuid.uuid4()))

    client = boto3.client("bedrock-agentcore", region_name=REGION)

    print(f"HarnessArn: {HARNESS_ARN}")
    print(f"SessionId : {session_id}")
    print("-" * 60)
    print("=== harness への送信内容 ===")
    print(prompt)
    print()
    print("=== harness からの応答 ===")
    invoke_harness(client, prompt, session_id)


if __name__ == "__main__":
    main()
