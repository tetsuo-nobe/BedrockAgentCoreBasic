"""AsyncAgent (AgentCore Runtime) を呼び出すクライアントスクリプト。

非同期 / 長時間実行の 2 つの操作を試せる:
  - start  : 非同期ジョブを開始する。即座に status が返る (実行環境を維持 = HealthyBusy)。
  - status : 実行中の非同期ジョブ (active_count / running_jobs) を問い合わせる。

Runtime ARN とリージョンの指定 (以下の優先順で解決する):
  1. コマンドライン引数 --arn / --region
  2. 環境変数 AGENT_RUNTIME_ARN / AWS_REGION (または AWS_DEFAULT_REGION)
  3. リージョンは、指定が無ければ ARN 文字列から推測する

    # 環境変数で ARN を渡す例 (PowerShell)
    $env:AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:<account-id>:runtime/<runtime-id>"
    python invoke.py start --duration 60 --session-id longrun-session-0001-0000000000000000

    # 引数で ARN を渡す例
    python invoke.py status --arn "arn:aws:bedrock-agentcore:us-east-1:<account-id>:runtime/<runtime-id>" \
        --session-id longrun-session-0001-0000000000000000

ARN は `agentcore status` で取得できる。

前提:
  - AWS 認証情報が設定済み (aws configure / 環境変数 など)。
  - boto3 に bedrock-agentcore クライアントが含まれるバージョンであること。
"""

import argparse
import json
import os
import sys
import time
import uuid

import boto3


def _resolve_arn(cli_arn: str | None) -> str:
    """Runtime ARN を解決する (引数 > 環境変数)。見つからなければエラー終了する。"""
    arn = cli_arn or os.environ.get("AGENT_RUNTIME_ARN")
    if not arn:
        sys.exit(
            "エラー: Runtime ARN が指定されていません。\n"
            "  --arn で指定するか、環境変数 AGENT_RUNTIME_ARN を設定してください。\n"
            "  ARN は `agentcore status` で取得できます。"
        )
    return arn


def _resolve_region(cli_region: str | None, arn: str) -> str:
    """リージョンを解決する (引数 > 環境変数 > ARN から推測)。"""
    region = cli_region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if region:
        return region
    # ARN 形式: arn:aws:bedrock-agentcore:<region>:<account-id>:runtime/<runtime-id>
    parts = arn.split(":")
    if len(parts) >= 4 and parts[3]:
        return parts[3]
    sys.exit(
        "エラー: リージョンを解決できませんでした。\n"
        "  --region で指定するか、環境変数 AWS_REGION を設定してください。"
    )


def _new_session_id() -> str:
    """runtimeSessionId は 33 文字以上が必要なため UUID ベースで生成する。"""
    return f"session-{uuid.uuid4().hex}"


def invoke(payload: dict, session_id: str, arn: str, region: str) -> str:
    """InvokeAgentRuntime を呼び出し、レスポンス本文を文字列で返す。"""
    client = boto3.client("bedrock-agentcore", region_name=region)

    t0 = time.time()
    response = client.invoke_agent_runtime(
        agentRuntimeArn=arn,
        runtimeSessionId=session_id,
        qualifier="DEFAULT",
        payload=json.dumps(payload).encode("utf-8"),
    )
    t1 = time.time()
    print(f"[invoke] invoke_agent_runtime() returned in {t1 - t0:.2f}s")

    # レスポンス本文を連結してデコードする
    body = b""
    for chunk in response.get("response", []):
        body += chunk if isinstance(chunk, bytes) else bytes(chunk)
    t2 = time.time()
    print(f"[invoke] response body read in {t2 - t1:.2f}s (total {t2 - t0:.2f}s)")
    return body.decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke the AsyncAgent AgentCore Runtime")
    parser.add_argument(
        "action",
        choices=["start", "status"],
        help="start=非同期ジョブ開始 / status=ジョブ状態確認",
    )
    parser.add_argument(
        "--arn",
        default=None,
        help="Runtime ARN。省略時は環境変数 AGENT_RUNTIME_ARN を使用する。",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS リージョン。省略時は環境変数 AWS_REGION、または ARN から推測する。",
    )
    parser.add_argument(
        "--prompt",
        default="3 と 5 を足して結果を教えて",
        help="エージェントへのプロンプト (start で使用)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="非同期ジョブの意図的な遅延秒数 (start で使用)。0 (デフォルト) は遅延なし。",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="runtimeSessionId (33 文字以上)。省略時は自動生成。"
        "状態確認では start 時と同じ値を指定すること。",
    )
    args = parser.parse_args()

    arn = _resolve_arn(args.arn)
    region = _resolve_region(args.region, arn)
    session_id = args.session_id or _new_session_id()

    if args.action == "start":
        payload = {"action": "start", "prompt": args.prompt, "duration": args.duration}
    else:  # status
        payload = {"action": "status"}

    print(f"[invoke] action={args.action} region={region} session_id={session_id}")
    print(f"[invoke] payload={json.dumps(payload, ensure_ascii=False)}")

    result = invoke(payload, session_id, arn, region)

    print("[invoke] response:")
    print(result)


if __name__ == "__main__":
    main()
