"""AgentCore Memory の短期記憶(イベント)を AgentCore Python SDK で確認するサンプル。

MemorySessionManager 経由で add_turns で会話イベントを書き込み、list_events で取得します。
メモリIDは環境変数 MEMORY_ID から取得します(メモリは事前作成済みが前提)。
"""

import os
import sys
import uuid

from bedrock_agentcore.memory import MemorySessionManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole

# 事前作成済みの AgentCore Memory リソースID (環境変数から取得)
MEMORY_ID = os.environ.get("MEMORY_ID")

# AWSリージョン (未指定時は東京リージョンを既定値とする)
REGION = os.environ.get("AWS_REGION", "ap-northeast-1")


def main() -> None:
    if not MEMORY_ID:
        print("エラー: 環境変数 MEMORY_ID が設定されていません。", file=sys.stderr)
        print('例 (PowerShell): $env:MEMORY_ID = "mem-xxxxxxxxxx"', file=sys.stderr)
        sys.exit(1)

    # MemorySessionManager がメモリID単位の操作の起点となる
    manager = MemorySessionManager(memory_id=MEMORY_ID, region_name=REGION)

    # actor(ユーザー) と session(会話) の識別子。
    # 実行するたびに新しい会話として扱われるよう、一意なIDを生成する。
    actor_id = f"sample-user-{uuid.uuid4().hex[:8]}"
    session_id = f"sample-session-{uuid.uuid4().hex[:8]}"

    print(f"MemoryId  : {MEMORY_ID}")
    print(f"ActorId   : {actor_id}")
    print(f"SessionId : {session_id}")
    print("-" * 60)

    # actor_id / session_id をひも付けたセッションを作成すると、
    # 以降のメソッド呼び出しでIDを毎回渡す必要がなくなる。
    session = manager.create_memory_session(actor_id=actor_id, session_id=session_id)

    # ------------------------------------------------------------
    # 1. 短期記憶へのイベント書き込み (add_turns)
    #    会話のやり取りを1ターンずつイベントとして記録する
    # ------------------------------------------------------------
    conversation = [
        ConversationalMessage("こんにちは。旅行の相談をしたいです。", MessageRole.USER),
        ConversationalMessage("かしこまりました。ご希望の行き先はありますか?", MessageRole.ASSISTANT),
        ConversationalMessage("沖縄に行きたいです。予算は10万円くらいです。", MessageRole.USER),
        ConversationalMessage("承知しました。沖縄旅行のプランをご提案します。", MessageRole.ASSISTANT),
    ]

    print("[1] イベントを書き込みます (add_turns)")
    for message in conversation:
        event = session.add_turns(messages=[message])
        print(f"  - [{message.role.value}] {message.text}  (eventId={event.eventId})")

    print("-" * 60)

    # ------------------------------------------------------------
    # 2. 短期記憶からのイベント取得 (list_events)
    #    書き込んだ会話履歴が取得できることを確認する
    # ------------------------------------------------------------
    print("[2] イベントを取得します (list_events)")
    events = session.list_events(max_results=20)

    # list_events は新しい順で返るため、会話順に表示するため反転する
    for event in reversed(events):
        for item in event.payload:
            conv = item.get("conversational")
            if conv:
                role = conv.get("role")
                text = conv.get("content", {}).get("text")
                print(f"  - [{role}] {text}")

    print("-" * 60)
    print(f"取得件数: {len(events)} 件 (短期記憶として保存されていることを確認できました)")


if __name__ == "__main__":
    main()
