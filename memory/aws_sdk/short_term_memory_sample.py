"""AgentCore Memory の短期記憶(イベント)を AWS SDK (boto3) で確認するサンプル。

CreateEvent で会話イベントを書き込み、ListEvents で取得します。
メモリIDは環境変数 MEMORY_ID から取得します(メモリは事前作成済みが前提)。
"""

import os
import sys
import uuid
from datetime import datetime, timezone

import boto3

# ------------------------------------------------------------
# 設定値
# ------------------------------------------------------------
# 事前作成済みの AgentCore Memory リソースID (環境変数から取得)
MEMORY_ID = os.environ.get("MEMORY_ID")

# AWSリージョン (未指定時は東京リージョンを既定値とする)
REGION = os.environ.get("AWS_REGION", "ap-northeast-1")


def main() -> None:
    if not MEMORY_ID:
        print("エラー: 環境変数 MEMORY_ID が設定されていません。", file=sys.stderr)
        print('例 (PowerShell): $env:MEMORY_ID = "mem-xxxxxxxxxx"', file=sys.stderr)
        sys.exit(1)

    # データプレーン用クライアント(イベントの書き込み・取得に使用)
    data_client = boto3.client("bedrock-agentcore", region_name=REGION)

    # actor(ユーザー) と session(会話) の識別子。
    # 実行するたびに新しい会話として扱われるよう、一意なIDを生成する。
    actor_id = f"sample-user-{uuid.uuid4().hex[:8]}"
    session_id = f"sample-session-{uuid.uuid4().hex[:8]}"

    print(f"MemoryId  : {MEMORY_ID}")
    print(f"ActorId   : {actor_id}")
    print(f"SessionId : {session_id}")
    print("-" * 60)

    # ------------------------------------------------------------
    # 1. 短期記憶へのイベント書き込み (CreateEvent)
    #    会話のやり取りを1ターンずつイベントとして記録する
    # ------------------------------------------------------------
    conversation = [
        ("こんにちは。旅行の相談をしたいです。", "USER"),
        ("かしこまりました。ご希望の行き先はありますか?", "ASSISTANT"),
        ("沖縄に行きたいです。予算は10万円くらいです。", "USER"),
        ("承知しました。沖縄旅行のプランをご提案します。", "ASSISTANT"),
    ]

    print("[1] イベントを書き込みます (CreateEvent)")
    for text, role in conversation:
        response = data_client.create_event(
            memoryId=MEMORY_ID,
            actorId=actor_id,
            sessionId=session_id,
            eventTimestamp=datetime.now(timezone.utc),
            payload=[
                {
                    "conversational": {
                        "content": {"text": text},
                        "role": role,
                    }
                }
            ],
        )
        event_id = response["event"]["eventId"]
        print(f"  - [{role}] {text}  (eventId={event_id})")

    print("-" * 60)

    # ------------------------------------------------------------
    # 2. 短期記憶からのイベント取得 (ListEvents)
    #    書き込んだ会話履歴が取得できることを確認する
    # ------------------------------------------------------------
    print("[2] イベントを取得します (ListEvents)")
    response = data_client.list_events(
        memoryId=MEMORY_ID,
        actorId=actor_id,
        sessionId=session_id,
        includePayloads=True,
        maxResults=20,
    )

    events = response.get("events", [])
    # ListEvents は新しい順で返るため、会話順に表示するため反転する
    for event in reversed(events):
        for item in event.get("payload", []):
            conv = item.get("conversational")
            if conv:
                role = conv.get("role")
                text = conv.get("content", {}).get("text")
                print(f"  - [{role}] {text}")

    print("-" * 60)
    print(f"取得件数: {len(events)} 件 (短期記憶として保存されていることを確認できました)")


if __name__ == "__main__":
    main()
