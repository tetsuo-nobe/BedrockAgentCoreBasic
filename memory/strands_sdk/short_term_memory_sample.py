"""AgentCore Memory の短期記憶(イベント)を Strands Agents SDK 統合で確認するサンプル。

AgentCoreMemorySessionManager を Strands の Agent に渡すと、会話の書き込みが自動化される。
メモリIDは環境変数 MEMORY_ID から取得します(メモリは事前作成済みが前提)。
"""

import json
import os
import sys
import uuid

from strands import Agent
from bedrock_agentcore.memory import MemorySessionManager
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# 事前作成済みの AgentCore Memory リソースID (環境変数から取得)
MEMORY_ID = os.environ.get("MEMORY_ID")

# AWSリージョン (未指定時は東京リージョンを既定値とする)
REGION = os.environ.get("AWS_REGION", "ap-northeast-1")


def main() -> None:
    if not MEMORY_ID:
        print("エラー: 環境変数 MEMORY_ID が設定されていません。", file=sys.stderr)
        print('例 (PowerShell): $env:MEMORY_ID = "mem-xxxxxxxxxx"', file=sys.stderr)
        sys.exit(1)

    # actor(ユーザー) と session(会話) の識別子。
    # 実行するたびに新しい会話として扱われるよう、一意なIDを生成する。
    actor_id = f"sample-user-{uuid.uuid4().hex[:8]}"
    session_id = f"sample-session-{uuid.uuid4().hex[:8]}"

    print(f"MemoryId  : {MEMORY_ID}")
    print(f"ActorId   : {actor_id}")
    print(f"SessionId : {session_id}")
    print("-" * 60)

    # ------------------------------------------------------------
    # 1. Strands Agent に会話させる
    #    session_manager を渡すことで、ユーザー発言・アシスタント応答が
    #    自動的に短期記憶(イベント)として書き込まれる
    # ------------------------------------------------------------
    config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=session_id,
        actor_id=actor_id,
    )

    print("[1] Agent と会話します (session_manager が自動でイベントを書き込む)")
    with AgentCoreMemorySessionManager(config, region_name=REGION) as session_manager:
        # callback_handler=None: 既定では応答をトークン単位でstdoutへ逐次出力してしまい、
        # 下の print(f"[ASSISTANT] ...") の表示が改行されずに混ざって見える。
        # ここでは応答内容をまとめて自分でprintしたいので、既定のストリーミング出力を無効化する。
        agent = Agent(
            system_prompt="あなたは旅行相談に応じるアシスタントです。",
            session_manager=session_manager,
            callback_handler=None,
        )

        user_inputs = [
            "こんにちは。旅行の相談をしたいです。",
            "沖縄に行きたいです。予算は10万円くらいです。",
        ]
        for text in user_inputs:
            print(f"  - [USER] {text}")
            response = agent(text)
            print(f"  - [ASSISTANT] {response}")
    # with ブロックを抜けると、バッファに残っているメッセージがフラッシュされる

    print("-" * 60)

    # ------------------------------------------------------------
    # 2. 短期記憶からのイベント取得 (list_events)
    #    Agent との会話が短期記憶に書き込まれていることを確認する
    #    (取得には AgentCore SDK の MemorySessionManager を使用)
    # ------------------------------------------------------------
    print("[2] イベントを取得します (list_events)")
    manager = MemorySessionManager(memory_id=MEMORY_ID, region_name=REGION)
    session = manager.create_memory_session(actor_id=actor_id, session_id=session_id)
    events = session.list_events(max_results=20)

    # list_events は新しい順で返るため、会話順に表示するため反転する
    #
    # Strands統合はテキストをそのまま payload に入れるのではなく、
    # Strands の SessionMessage 全体を JSON 文字列化して conversational.content.text に格納する。
    # そのため取得時は、text を json.loads してから実際の発言内容(message.content)を取り出す必要がある。
    for event in reversed(events):
        for item in event.payload:
            conv = item.get("conversational")
            if conv:
                session_message = json.loads(conv["content"]["text"])
                role = session_message["message"]["role"]
                text = "".join(
                    block.get("text", "") for block in session_message["message"].get("content", [])
                )
                print(f"  - [{role}] {text}")

    print("-" * 60)
    print(f"取得件数: {len(events)} 件 (短期記憶として保存されていることを確認できました)")


if __name__ == "__main__":
    main()
