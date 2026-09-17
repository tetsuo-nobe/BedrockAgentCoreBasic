"""AgentCore Memory の長期記憶(User Preference戦略)を Strands Agents SDK 統合で確認するサンプル。

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
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# 事前作成済みの AgentCore Memory リソースID (環境変数から取得)
MEMORY_ID = os.environ.get("MEMORY_ID")

# AWSリージョン (未指定時は東京リージョンを既定値とする)
REGION = os.environ.get("AWS_REGION", "ap-northeast-1")

# 長期記憶の抽出が完了するまで待つ秒数。
# 抽出は非同期で行われるため、書き込み直後にはまだ長期記憶に反映されていない場合がある。
# 実測では1回目のセッション終了から抽出完了まで約90秒かかるケースが確認されているため、
# 30秒では抽出前に2回目のセッションが始まってしまい、コンテキストが注入されないことがある。
WAIT_SECONDS_FOR_EXTRACTION = 90

# AgentCoreMemorySessionManager は、関連する長期記憶をユーザー発言に
# <user_context>...</user_context> タグとして埋め込むだけで、それを「使うように」とは
# 指示しない。system_prompt側で明示的に「ユーザーについて知っていることを活用する」ことを
# 指示しておかないと、モデルが埋め込まれたコンテキストを無視してしまうことがある。
SYSTEM_PROMPT = (
    "あなたは親しみやすいアシスタントです。"
    "ユーザーの発言に<user_context>タグで過去の好みの情報が含まれている場合は、"
    "それを踏まえて回答してください。"
)


def get_user_preference_strategy(memory_client: MemoryClient) -> dict:
    """メモリに設定されている User Preference戦略の情報を取得する。

    このメモリに実際に設定されている名前空間テンプレート (namespaceTemplates/namespaces) は、
    メモリ作成時の設定内容次第で SDK の既定値 (/strategies/{memoryStrategyId}/actors/{actorId}/)
    とは異なる場合がある。そのため、SDKの既定値を仮定せず、get_memory_strategies() で
    実際のテンプレートを取得して使う。
    """
    strategies = memory_client.get_memory_strategies(memory_id=MEMORY_ID)
    for strategy in strategies:
        if strategy.get("memoryStrategyType") == "USER_PREFERENCE":
            # namespaceTemplates (新) / namespaces (旧、非推奨) のどちらのキーで
            # 返ってくる場合もあるため、両方を見る。
            if "namespaceTemplates" not in strategy and "namespaces" in strategy:
                strategy["namespaceTemplates"] = strategy["namespaces"]
            return strategy
    raise RuntimeError(
        "このメモリには User Preference戦略が設定されていません。"
        "agentcore add memory --strategies USER_PREFERENCE 等で設定してください。"
    )


def build_session_manager(
    actor_id: str, session_id: str, strategy: dict
) -> AgentCoreMemorySessionManager:
    """actor_id / session_id / strategy (get_memory_strategiesの戻り値) を指定して
    session_manager を作成する。

    retrieval_config のキーには、このメモリに実際に設定されている名前空間テンプレートを
    そのまま使う。{memoryStrategyId} が含まれる場合は RetrievalConfig(strategy_id=...) を
    指定することで実際のIDに解決される。
    """
    namespace_template = strategy["namespaceTemplates"][0]
    strategy_id = strategy["memoryStrategyId"]

    # relevance_score は検索結果をどの程度厳しく絞り込むかの閾値(0.0〜1.0)。
    # 高すぎると関連する長期記憶が絞り込まれすぎてコンテキストに注入されなくなるため、
    # 学習用サンプルでは低めの値にしている。
    retrieval_config = {
        namespace_template: RetrievalConfig(top_k=5, relevance_score=0.0, strategy_id=strategy_id),
    }

    config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config=retrieval_config,
    )
    return AgentCoreMemorySessionManager(config, region_name=REGION)


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

    # メモリに設定されている User Preference戦略の実際の情報(strategyId・名前空間)を取得する。
    memory_client = MemoryClient(region_name=REGION)
    strategy = get_user_preference_strategy(memory_client)
    strategy_id = strategy["memoryStrategyId"]
    namespace_template = strategy["namespaceTemplates"][0]

    print(f"MemoryId         : {MEMORY_ID}")
    print(f"StrategyId       : {strategy_id}")
    print(f"NamespaceTemplate: {namespace_template}")
    print(f"ActorId          : {actor_id}")
    print(f"SessionId(1回目) : {session_id_1}")
    print(f"SessionId(2回目) : {session_id_2}")
    print("-" * 60)

    # ------------------------------------------------------------
    # 1. 1回目のセッション: ユーザーの好みを伝える
    #    スポーツ・ファッション・映画それぞれについて話し、
    #    User Preference戦略が複数のジャンルの好みを抽出できるか確認する
    # ------------------------------------------------------------
    print("[1] 1回目のセッションで好みを伝えます")
    with build_session_manager(actor_id, session_id_1, strategy) as session_manager:
        # callback_handler=None: 既定では応答をトークン単位でstdoutへ逐次出力してしまい、
        # 下の print(f"[ASSISTANT] ...") の表示が改行されずに混ざって見える。
        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            session_manager=session_manager,
            callback_handler=None,
        )

        user_inputs = [
            "スポーツ観戦が好きで、特にサッカーをよく見ます。海外サッカーも好きです。",
            "ファッションはシンプルなモノトーンの服が好きです。派手な柄は苦手です。",
            "映画はSF映画が好きです。特にクリストファー・ノーラン監督の作品が好きです。",
        ]
        for text in user_inputs:
            print(f"  - [USER] {text}")
            response = agent(text)
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
    # namespace_template ("/strategies/{memoryStrategyId}/actors/{actorId}/" 等) の
    # プレースホルダーを実際の値に置き換えて、正確な名前空間を指定する。
    resolved_namespace = namespace_template.format(
        memoryStrategyId=strategy_id, actorId=actor_id, sessionId=session_id_1
    )
    records = memory_client.retrieve_memories(
        memory_id=MEMORY_ID,
        namespace_path=resolved_namespace,
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
    #    session_manager の retrieval_config により、Agent への問いかけ時に
    #    関連する長期記憶が自動的にコンテキストへ注入される
    # ------------------------------------------------------------
    print("[4] 2回目のセッション(別session_id)で、好みを覚えているか確認します")
    with build_session_manager(actor_id, session_id_2, strategy) as session_manager:
        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            session_manager=session_manager,
            callback_handler=None,
        )

        text = "今週末に観る映画を探しています。私の好みにマッチする、おすすめの映画はありますか?"
        print(f"  - [USER] {text}")
        response = agent(text)
        print(f"  - [ASSISTANT] {response}")

    print("-" * 60)
    print("応答が1回目に伝えた好み(サッカー・モノトーンファッション・ノーラン監督のSF映画)を")
    print("踏まえたものになっていれば、長期記憶(User Preference戦略)が")
    print("セッションをまたいで反映されていることを確認できます。")


if __name__ == "__main__":
    main()
