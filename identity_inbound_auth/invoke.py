"""
AgentCore Runtime (JWT インバウンド認証) を呼び出すサンプルコード

このエージェント（main (1).py 等でデプロイした AgentCore Runtime）は
AgentCore Identity の JWT ベアラートークン認証（customJWTAuthorizer）で
インバウンド認証が構成されていることを前提とする。

JWT 認証が構成された Runtime は boto3 の invoke_agent_runtime を
使用できないため（boto3 は SigV4 専用）、本スクリプトは
InvokeAgentRuntime を HTTPS リクエストとして直接呼び出す。
参考: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-oauth.html

前提:
- アクセストークン（JWT）は環境変数 TOKEN にすでに設定済みであること
  （Cognito 等での取得はこのスクリプトの範囲外）
- .env に以下を設定していること
    ARN       : 呼び出す AgentCore Runtime の ARN
    REGION    : Runtime のリージョン（既定値 us-west-2）
    TOKEN     : アクセストークン（JWT）
    QUALIFIER : （任意）呼び出すエンドポイント名。省略時は DEFAULT

実行:
    python invoke.py "こんにちは"
    # 引数を省略すると既定のプロンプトを送信する
"""

import json
import os
import sys
import uuid
from urllib.parse import quote

import requests
from dotenv import load_dotenv

# .env ファイルの内容を読み込む
load_dotenv()

REGION = os.environ.get("REGION", "us-west-2")
ARN = os.environ.get("ARN")
QUALIFIER = os.environ.get("QUALIFIER", "DEFAULT")


def invoke_agent_runtime(prompt, access_token, session_id=None):
    """InvokeAgentRuntime を HTTPS リクエストとして呼び出し、レスポンスを返す。

    JWT 認証が構成された AgentCore Runtime は boto3 の
    invoke_agent_runtime（SigV4 専用）が使えないため、
    Authorization: Bearer ヘッダーを付与した HTTPS リクエストを直接送る。
    """
    if not ARN:
        raise ValueError("環境変数 ARN が設定されていません")

    # runtimeSessionId は 33 文字以上である必要がある
    session_id = session_id or str(uuid.uuid4()) + str(uuid.uuid4())

    # ARN は URL エンコードしてパスに含める
    escaped_arn = quote(ARN, safe="")
    url = (
        f"https://bedrock-agentcore.{REGION}.amazonaws.com"
        f"/runtimes/{escaped_arn}/invocations"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
    }
    params = {"qualifier": QUALIFIER}
    payload = json.dumps({"prompt": prompt})

    response = requests.post(
        url, headers=headers, params=params, data=payload, stream=True
    )

    if response.status_code == 401:
        # OAuth エラー時は WWW-Authenticate ヘッダーに詳細が入っている
        raise RuntimeError(
            f"認証エラー (401): {response.headers.get('WWW-Authenticate')}"
        )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "text/event-stream" in content_type:
        # ストリーミングレスポンス（SSE 形式）を逐次表示する
        chunks = []
        for line in response.iter_lines(chunk_size=10):
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                decoded = decoded[len("data: "):]
                print(decoded)
                chunks.append(decoded)
        return "\n".join(chunks)

    # JSON レスポンスの場合
    return response.text


def main():
    # コマンドライン引数があればそれをプロンプトにする。なければ既定値。
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "こんにちは"

    access_token = os.environ.get("TOKEN")
    if not access_token:
        raise ValueError("環境変数 TOKEN が設定されていません")

    result = invoke_agent_runtime(prompt, access_token)

    print("=== エージェントからの応答 ===")
    print(result)


if __name__ == "__main__":
    main()
