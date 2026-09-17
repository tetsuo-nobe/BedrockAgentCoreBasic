"""AgentCore Memory の長期記憶(User Preference戦略)を Strands hooks + AgentCore SDK で確認するサンプル。

パターン4: AgentCoreMemorySessionManager(パターン3)のような既製品を使うのではなく、
Strands の汎用フック機構 (HookProvider) を自分で実装し、長期記憶の検索・保存を行う。

実装は AWS公式ワークショップのノートブック (CustomerSupportMemoryHooks) の設計を参考にしている。
    - MessageAddedEvent: ユーザー発言の直前に長期記憶を検索し、コンテキストとして注入する
    - AfterInvocationEvent: 応答が完了した後に、そのやり取りをAgentCore Memoryへ保存する

1回目の会話でユーザーの好み(好きなスポーツ・ファッションの好み・好きな映画)を伝え、
少し待ってから actor_id はそのまま・session_id だけ変えて2回目の会話を行う。
2回目のセッションで、映画のおすすめを尋ねたときに Agent が過去に伝えた好みを
踏まえた回答をするかどうかを確認する。

前提:
    - AgentCore Memory リソースが作成済みで、User Preference (userPreferenceMemoryStrategy) 戦略が
      設定されていること
    - 環境変数 MEMORY_ID にメモリID が設定されていること
    - AWS認証情報・Bedrock モデルへのアクセス権が設定済みであること
"""

import os
import sys
import time
import uuid

from strands import Agent
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterInvocationEvent, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient

# 事前作成済みの AgentCore Memory リソースID (環境変数から取得)
MEMORY_ID = os.environ.get("MEMORY_ID")

# AWSリージョン (未指定時は東京リージョンを既定値とする)
REGION = os.environ.get("AWS_REGION", "ap-northeast-1")

# 長期記憶の抽出が完了するまで待つ秒数。
# 抽出は非同期で行われるため、書き込み直後にはまだ長期記憶に反映されていない場合がある。
WAIT_SECONDS_FOR_EXTRACTION = 90


class LongTermMemoryHook(HookProvider):
    """長期記憶(User Preference)の検索・保存を行う自作フック。

    ノートブックの CustomerSupportMemoryHooks と同じ2フック構成:
        - retrieve_customer_context (MessageAddedEvent): 応答前に関連する長期記憶を検索し、
          ユーザー発言の先頭にラベル付きテキストとして注入する
        - save_support_interaction (AfterInvocationEvent): 応答後に、今回のやり取りを
          AgentCore Memoryへ保存する
    """

    def __init__(self, memory_client: MemoryClient, memory_id: str, strategy: dict):
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.strategy_id = strategy["memoryStrategyId"]
        self.namespace_template = strategy["namespaceTemplates"][0]

    def _resolve_namespace(self, actor_id: str) -> str:
        # 名前空間テンプレート(例: "/strategies/{memoryStrategyId}/actors/{actorId}/")の
        # プレースホルダーを実際の値に置き換える。
        return self.namespace_template.format(memoryStrategyId=self.strategy_id, actorId=actor_id)

    def retrieve_customer_context(self, event: MessageAddedEvent) -> None:
        """応答前に、関連する長期記憶を検索してユーザー発言に注入する。"""
        messages = event.agent.messages
        last_message = messages[-1]
        # ユーザーの発言(ツール結果ではない)のみを処理する
        if last_message.get("role") != "user":
            return
        content = last_message.get("content", [])
        if not content or "text" not in content[0]:
            return

        actor_id = event.agent.state.get("actor_id")
        user_query = content[0]["text"]

        try:
            memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=self._resolve_namespace(actor_id),
                query=user_query,
                top_k=3,
            )
            context_items = []
            for memory in memories:
                if isinstance(memory, dict):
                    text = memory.get("content", {}).get("text", "").strip()
                    if text:
                        context_items.append(f"[USER_PREFERENCE] {text}")

            if context_items:
                context_text = "\n".join(context_items)
                original_text = content[0]["text"]
                content[0]["text"] = f"Customer Context:\n{context_text}\n\n{original_text}"
        except Exception as e:
            print(f"長期記憶の取得に失敗しました: {e}")

    def save_support_interaction(self, event: AfterInvocationEvent) -> None:
        """応答後に、直近のやり取り(ユーザー発言+アシスタント応答)をAgentCore Memoryへ保存する。"""
        try:
            messages = event.agent.messages
            if len(messages) < 2 or messages[-1].get("role") != "assistant":
                return

            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")

            customer_query = None
            agent_response = None
            for msg in reversed(messages):
                if msg.get("role") == "assistant" and agent_response is None:
                    agent_response = "".join(b.get("text", "") for b in msg.get("content", []))
                elif msg.get("role") == "user" and customer_query is None:
                    customer_query = "".join(b.get("text", "") for b in msg.get("content", []))
                    break

            if customer_query and agent_response:
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    messages=[(customer_query, "USER"), (agent_response, "ASSISTANT")],
                )
        except Exception as e:
            print(f"長期記憶への保存に失敗しました: {e}")

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(MessageAddedEvent, self.retrieve_customer_context)
        registry.add_callback(AfterInvocationEvent, self.save_support_interaction)


def get_user_preference_strategy(memory_client: MemoryClient) -> dict:
    """メモリに設定されている User Preference戦略の情報を取得する。

    このメモリに実際に設定されている名前空間テンプレートは、メモリ作成時の設定内容次第で
    変わるため、値を仮定せず get_memory_strategies() で実際のテンプレートを取得して使う。
    """
    strategies = memory_client.get_memory_strategies(memory_id=MEMORY_ID)
    for strategy in strategies:
        if strategy.get("memoryStrategyType") == "USER_PREFERENCE":
            if "namespaceTemplates" not in strategy and "namespaces" in strategy:
                strategy["namespaceTemplates"] = strategy["namespaces"]
            return strategy
    raise RuntimeError(
        "このメモリには User Preference戦略が設定されていません。"
        "agentcore add memory --strategies USER_PREFERENCE 等で設定してください。"
    )


def build_agent(memory_hook: LongTermMemoryHook, actor_id: str, session_id: str) -> Agent:
    # callback_handler=None: 既定では応答をトークン単位でstdoutへ逐次出力してしまい、
    # 下の print(f"[ASSISTANT] ...") の表示が改行されずに混ざって見える。
    return Agent(
        system_prompt="あなたは親しみやすいアシスタントです。",
        hooks=[memory_hook],
        state={"actor_id": actor_id, "session_id": session_id},
        callback_handler=None,
    )


def main() -> None:
    if not MEMORY_ID:
        print("エラー: 環境変数 MEMORY_ID が設定されていません。", file=sys.stderr)
        print('例 (PowerShell): $env:MEMORY_ID = "mem-xxxxxxxxxx"', file=sys.stderr)
        sys.exit(1)

    # actor(ユーザー) は2つのセッションで同じIDを使う。
    # session(会話) は1回目・2回目で別のIDにして、セッションをまたいで
    # 長期記憶(ユーザーの好み)が引き継がれることを確認する。
    actor_id = f"sample-user-{uuid.uuid4().hex[:8]}"
    session_id_1 = f"sample-session-1-{uuid.uuid4().hex[:8]}"
    session_id_2 = f"sample-session-2-{uuid.uuid4().hex[:8]}"

    memory_client = MemoryClient(region_name=REGION)
    strategy = get_user_preference_strategy(memory_client)
    memory_hook = LongTermMemoryHook(memory_client, MEMORY_ID, strategy)

    print(f"MemoryId         : {MEMORY_ID}")
    print(f"StrategyId       : {strategy['memoryStrategyId']}")
    print(f"NamespaceTemplate: {strategy['namespaceTemplates'][0]}")
    print(f"ActorId          : {actor_id}")
    print(f"SessionId(1回目) : {session_id_1}")
    print(f"SessionId(2回目) : {session_id_2}")
    print("-" * 60)

    # ------------------------------------------------------------
    # 1. 1回目のセッション: ユーザーの好みを伝える
    #    スポーツ・ファッション・映画それぞれについて話し、
    #    User Preference戦略が複数のジャンルの好みを抽出できるか確認する
    #    (AfterInvocationEventフックにより、各やり取りはAgentCore Memoryへ自動保存される)
    # ------------------------------------------------------------
    print("[1] 1回目のセッションで好みを伝えます")
    agent1 = build_agent(memory_hook, actor_id, session_id_1)

    user_inputs = [
        "スポーツ観戦が好きで、特にサッカーをよく見ます。海外サッカーも好きです。",
        "ファッションはシンプルなモノトーンの服が好きです。派手な柄は苦手です。",
        "映画はSF映画が好きです。特にクリストファー・ノーラン監督の作品が好きです。",
    ]
    for text in user_inputs:
        print(f"  - [USER] {text}")
        response = agent1(text)
        print(f"  - [ASSISTANT] {response}")

    print("-" * 60)

    # ------------------------------------------------------------
    # 2. 長期記憶への抽出を待つ
    #    User Preference戦略による抽出は非同期処理のため、少し待つ必要がある
    # ------------------------------------------------------------
    print(f"[2] 長期記憶への抽出を待ちます ({WAIT_SECONDS_FOR_EXTRACTION}秒)")
    time.sleep(WAIT_SECONDS_FOR_EXTRACTION)

    # ------------------------------------------------------------
    # 3. 長期記憶に抽出された内容を直接確認する (retrieve_memories)
    # ------------------------------------------------------------
    print("[3] 長期記憶から好みの情報を検索します (retrieve_memories)")
    records = memory_client.retrieve_memories(
        memory_id=MEMORY_ID,
        namespace=memory_hook._resolve_namespace(actor_id),
        query="好きなスポーツ・ファッションの好み・好きな映画",
        top_k=5,
    )
    if records:
        for record in records:
            content = record.get("content", {})
            print(f"  - {content.get('text', record)}")
    else:
        print("  - まだ長期記憶に反映されていないようです。待ち時間を増やして再実行してみてください。")

    print("-" * 60)

    # ------------------------------------------------------------
    # 4. 2回目のセッション: 別セッションで、好みを覚えているか確認する
    #    retrieve_customer_context フックにより、Agentへの問いかけ時に
    #    関連する長期記憶が自動的にコンテキストへ注入される
    # ------------------------------------------------------------
    print("[4] 2回目のセッション(別session_id)で、好みを覚えているか確認します")
    agent2 = build_agent(memory_hook, actor_id, session_id_2)

    text = "今週末に観る映画を探しています。私の好みにマッチする、おすすめの映画はありますか?"
    print(f"  - [USER] {text}")
    response = agent2(text)
    print(f"  - [ASSISTANT] {response}")

    print("-" * 60)
    print("応答が1回目に伝えた好み(サッカー・モノトーンファッション・ノーラン監督のSF映画)を")
    print("踏まえたものになっていれば、長期記憶(User Preference戦略)が")
    print("セッションをまたいで反映されていることを確認できます。")


if __name__ == "__main__":
    main()
