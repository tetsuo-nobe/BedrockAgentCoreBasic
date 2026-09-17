"""AgentCore Memory の短期記憶(イベント)を Strands hooks + AgentCore SDK で確認するサンプル。

パターン4: AgentCoreMemorySessionManager(パターン3)のような既製品を使うのではなく、
Strands の汎用フック機構 (HookProvider) を自分で実装し、その中で AgentCore SDK の
MemoryClient を呼び出して短期記憶の書き込み・取得を行う。

メモリIDは環境変数 MEMORY_ID から取得します(メモリは事前作成済みが前提)。
"""

import os
import sys
import uuid

from strands import Agent
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AgentInitializedEvent, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient

# 事前作成済みの AgentCore Memory リソースID (環境変数から取得)
MEMORY_ID = os.environ.get("MEMORY_ID")

# AWSリージョン (未指定時は東京リージョンを既定値とする)
REGION = os.environ.get("AWS_REGION", "ap-northeast-1")


class ShortTermMemoryHook(HookProvider):
    """短期記憶(イベント)の読み込み・書き込みを行う自作フック。

    - AgentInitializedEvent: Agent起動時に過去の会話履歴を読み込み、system_promptに注入する
    - MessageAddedEvent: メッセージが追加されるたびに、AgentCore Memoryへイベントとして書き込む

    パターン3(AgentCoreMemorySessionManager)がAWS公式の完成品であるのに対し、
    このフックは同じ処理を自分で実装したものになる。
    """

    def __init__(self, memory_client: MemoryClient, memory_id: str):
        self.memory_client = memory_client
        self.memory_id = memory_id

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)

    def on_agent_initialized(self, event: AgentInitializedEvent) -> None:
        """Agent起動時に、過去の会話履歴を読み込んでsystem_promptに注入する。"""
        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")

        turns = self.memory_client.get_last_k_turns(
            memory_id=self.memory_id,
            actor_id=actor_id,
            session_id=session_id,
            k=10,
        )
        if not turns:
            return

        lines = []
        for turn in turns:
            for message in turn:
                role = message.get("role")
                text = message.get("content", {}).get("text", "")
                lines.append(f"{role}: {text}")

        event.agent.system_prompt += "\n\n過去の会話履歴:\n" + "\n".join(lines)

    def on_message_added(self, event: MessageAddedEvent) -> None:
        """メッセージが追加されるたびに、AgentCore Memoryへイベントとして書き込む。"""
        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")

        role = event.message.get("role", "").upper()  # Strandsは小文字("user"), AgentCoreは大文字("USER")
        text = "".join(block.get("text", "") for block in event.message.get("content", []))
        if not text:
            return

        self.memory_client.create_event(
            memory_id=self.memory_id,
            actor_id=actor_id,
            session_id=session_id,
            messages=[(text, role)],
        )


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

    memory_client = MemoryClient(region_name=REGION)

    # ------------------------------------------------------------
    # 1. Strands Agent に会話させる
    #    ShortTermMemoryHook が MessageAddedEvent をフックして、
    #    ユーザー発言・アシスタント応答を自動的に短期記憶(イベント)として書き込む
    # ------------------------------------------------------------
    print("[1] Agent と会話します (自作フックが会話ごとにイベントを書き込む)")
    # callback_handler=None: 既定では応答をトークン単位でstdoutへ逐次出力してしまい、
    # 下の print(f"[ASSISTANT] ...") の表示が改行されずに混ざって見える。
    # ここでは応答内容をまとめて自分でprintしたいので、既定のストリーミング出力を無効化する。
    agent = Agent(
        system_prompt="あなたは旅行相談に応じるアシスタントです。",
        hooks=[ShortTermMemoryHook(memory_client, MEMORY_ID)],
        state={"actor_id": actor_id, "session_id": session_id},
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

    print("-" * 60)

    # ------------------------------------------------------------
    # 2. 短期記憶からのイベント取得 (list_events)
    #    Agent との会話が短期記憶に書き込まれていることを確認する
    # ------------------------------------------------------------
    print("[2] イベントを取得します (list_events)")
    events = memory_client.list_events(
        memory_id=MEMORY_ID,
        actor_id=actor_id,
        session_id=session_id,
        max_results=20,
    )

    # list_events は新しい順で返るため、会話順に表示するため反転する
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
