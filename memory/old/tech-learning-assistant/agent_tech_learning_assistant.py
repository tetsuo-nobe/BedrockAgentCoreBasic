import os
from datetime import datetime
from typing import List, Dict
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# グローバル設定
MEMORY_ID = os.getenv("MEMORY_ID")
REGION = os.getenv("REGION", "us-west-2")

# Memory Clientの初期化
memory_client = MemoryClient(region_name=REGION)

# カスタムツールの定義
@tool
def analyze_learning_progress(subject: str = None) -> str:
    """
    学習進捗を分析します。
    特定の技術分野を指定することもできます。
    """
    try:
        # 現在のユーザー情報を取得（グローバル変数から）
        actor_id = getattr(analyze_learning_progress, 'actor_id', 'current_user')

        # 技術知識の取得
        query = f"{subject} 学習" if subject else "学習した技術"
        knowledge_records = memory_client.retrieve_memories(
            memory_id=MEMORY_ID,
            namespace=f"tech_learning/knowledge/{actor_id}",
            query=query,
            top_k=10
        )

        records = knowledge_records
        if not records:
            return f"まだ{subject or '技術'}の学習記録がありません。学習を始めてみましょう！"

        # 分析結果の生成
        progress_info = []
        for record in records[:5]:  # 最新5件を表示
            content = record['content']['text']
            progress_info.append(f"・{content}")

        result = f"📊 {subject or '全体的'}の学習進捗:\n\n"
        result += "\n".join(progress_info)
        result += f"\n\n合計{len(records)}件の学習記録があります！"

        return result

    except Exception as e:
        return f"学習進捗の分析中にエラーが発生しました: {str(e)}"

@tool  
def identify_weak_areas() -> str:
    """苦手分野を特定します"""
    try:
        actor_id = getattr(identify_weak_areas, 'actor_id', 'current_user')

        # 学習傾向の取得
        preference_records = memory_client.retrieve_memories(
            memory_id=MEMORY_ID,
            namespace=f"tech_learning/preferences/{actor_id}",
            query="苦手 理解困難 課題",
            top_k=10
        )

        records = preference_records
        if not records:
            return "まだ十分な学習データがありません。もう少し学習を続けると、苦手分野の分析ができるようになります！"

        # 苦手分野の分析
        weak_areas = []
        for record in records:
            content = record['content']['text']
            weak_areas.append(f"・{content}")

        result = "🔍 苦手分野の分析結果:\n\n"
        result += "\n".join(weak_areas)
        result += "\n\n📈 改善提案:\n"
        result += "・基礎から段階的に学習を進めましょう\n"
        result += "・不明な点は遠慮なく質問してください"

        return result

    except Exception as e:
        return f"苦手分野の分析中にエラーが発生しました: {str(e)}"

@tool
def get_session_summary(session_id: str = None, full_content: bool = True, max_summaries: int = 3) -> str:
    """学習セッションのサマリーを取得します

    Args:
        session_id: 取得するセッションID（未指定の場合は現在のセッション）
        full_content: 完全な内容を表示するか（False の場合は200文字で切り詰め）
        max_summaries: 表示するサマリー数の上限
    """
    try:
        actor_id = getattr(get_session_summary, 'actor_id', 'current_user')

        # session_idが指定されていない場合は現在のセッションを使用
        if not session_id:
            session_id = getattr(get_session_summary, 'current_session_id', 'current_session')

        # セッションサマリーの取得
        summary_records = memory_client.retrieve_memories(
            memory_id=MEMORY_ID,
            namespace=f"tech_learning/summaries/{actor_id}/{session_id}",
            query="学習セッション サマリー",
            top_k=max(max_summaries, 5)
        )

        records = summary_records
        if not records:
            return f"セッション '{session_id}' のサマリーがまだ生成されていません。学習を続けると自動的にサマリーが作成されます！"

        # セッションサマリーの表示
        session_summaries = []
        for i, record in enumerate(records[:max_summaries]):
            content = record['content']['text']

            if full_content:
                # 完全な内容を表示（XMLタグの整形も含む）
                if content.strip().startswith('<summary>'):
                    # XMLサマリーの場合は構造化して表示
                    formatted_content = content.replace('<topic name="', '\n🎯 **').replace('">', '**\n   ')
                    formatted_content = formatted_content.replace('</topic>', '\n')
                    formatted_content = formatted_content.replace('<summary>', '').replace('</summary>', '')
                    session_summaries.append(f"📋 **サマリー {i+1}:**{formatted_content}")
                else:
                    session_summaries.append(f"📋 **サマリー {i+1}:**\n{content}")
            else:
                # 200文字で切り詰め
                session_summaries.append(f"📋 {content[:200]}...")

        result = f"📊 セッション '{session_id}' のサマリー:\n\n"
        result += "\n".join(session_summaries)
        result += f"\n\n💡 このサマリーは学習内容を効率的に振り返るのに役立ちます！"
        result += f"\n（表示件数: {len(session_summaries)}/{len(records)}件）"

        return result

    except Exception as e:
        return f"セッションサマリーの取得中にエラーが発生しました: {str(e)}"

@tool
def suggest_review_topics() -> str:
    """復習すべきトピックを提案します"""
    try:
        actor_id = getattr(suggest_review_topics, 'actor_id', 'current_user')

        # 過去の学習内容から復習候補を検索
        knowledge_records = memory_client.retrieve_memories(
            memory_id=MEMORY_ID,
            namespace=f"tech_learning/knowledge/{actor_id}",
            query="復習 理解 概念",
            top_k=15
        )

        records = knowledge_records
        if not records:
            return "まだ復習できる学習記録がありません。継続して学習を進めましょう！"

        # 復習トピックの提案
        review_topics = []
        for i, record in enumerate(records[:5]):  # 上位5件を提案
            content = record['content']['text']
            review_topics.append(f"{i+1}. {content}")

        result = "📚 復習におすすめのトピック:\n\n"
        result += "\n".join(review_topics)
        result += "\n\n💡 復習のコツ:\n"
        result += "・まずは概念を思い出してから、詳細を確認\n"
        result += "・実際にコードを書いて動作確認\n"
        result += "・理解が曖昧な部分は質問してください"

        return result

    except Exception as e:
        return f"復習トピックの検索中にエラーが発生しました: {str(e)}"

# メモリ管理のヘルパー関数
def save_conversation_to_memory(memory_id: str, actor_id: str, session_id: str, 
                               user_message: str, assistant_message: str):
    """会話をメモリに保存"""
    try:
        memory_client.create_event(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            messages=[
                (user_message, "USER"),
                (assistant_message, "ASSISTANT")
            ]
        )
        print("✅ 会話をメモリに保存しました")
    except Exception as e:
        print(f"❌ メモリ保存エラー: {e}")

def load_conversation_history(memory_id: str, actor_id: str, session_id: str, max_results: int = 10):
    """過去の会話履歴を取得"""
    try:
        events = memory_client.list_events(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            max_results=max_results
        )

        # イベントを時系列順にソート（直接リストが返される）
        sorted_events = sorted(events, key=lambda x: x['eventTimestamp'])

        # 会話履歴を構築（Strandsエージェント用の正しい形式）
        history_messages = []
        for event in sorted_events:
            for item in event.get('payload', []):
                if 'conversational' in item:
                    conv = item['conversational']
                    history_messages.append({
                        "role": conv['role'].lower(),
                        "content": [{"text": conv['content']['text']}]
                    })

        return history_messages

    except Exception as e:
        print(f"⚠️ 履歴取得エラー: {e}")
        return []

# BedrockAgentCoreアプリケーション
app = BedrockAgentCoreApp()

# エージェントのグローバル変数
agent = None

@app.entrypoint
async def tech_learning_assistant(payload):
    """技術学習アシスタントのエントリーポイント"""
    global agent

    print("🎓 技術学習アシスタントを起動中...")

    # ペイロードから情報取得
    user_input = payload.get("message") or payload.get("prompt", "こんにちは")
    actor_id = payload.get("actor_id", "default_user")
    session_id = payload.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # ツールのactor_idとsession_idを設定（グローバル変数として）
    analyze_learning_progress.actor_id = actor_id
    identify_weak_areas.actor_id = actor_id
    suggest_review_topics.actor_id = actor_id
    get_session_summary.actor_id = actor_id
    get_session_summary.current_session_id = session_id

    # 初回のみ初期化
    if agent is None:
        print("エージェントを初期化中...")

        # 環境変数からモデルIDを取得
        model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")

        model = BedrockModel(
            model_id=model_id,
            params={"max_tokens": 4096, "temperature": 0.7},
            region="us-west-2"
        )

        # エージェントの初期化
        agent = Agent(
            model=model,
            tools=[
                analyze_learning_progress,
                identify_weak_areas,
                suggest_review_topics,
                get_session_summary
            ],
            system_prompt="""あなたは優秀な技術学習アシスタントです。
            エンジニアの技術学習をサポートし、理解度を記録し、効果的な学習方法を提案します。

            以下のツールが利用可能です：
            - analyze_learning_progress: 学習進捗を分析（特定の技術分野も指定可能）
            - identify_weak_areas: 苦手分野を特定
            - suggest_review_topics: 復習すべきトピックを提案
            - get_session_summary: 学習セッションのサマリーを取得

            以下の点に注意してください：
            - 技術的な質問には具体的な例を交えて説明する
            - 理解度を確認しながら進める
            - 苦手分野を特定したら、それに応じた学習方法を提案する
            - 励ましと建設的なフィードバックを提供する
            - 必要に応じてツールを活用して学習状況を把握する
            """
        )
        print("✅ エージェント初期化完了！")

    print(f"👤 ユーザー: {actor_id}")
    print(f"📝 セッション: {session_id}")
    print(f"💬 質問: {user_input}")

    try:
        # 過去の会話履歴を取得
        print("📚 過去の学習履歴を取得中...")
        history_messages = load_conversation_history(MEMORY_ID, actor_id, session_id, max_results=10)

        if history_messages:
            print(f"✅ {len(history_messages)}件の過去メッセージを取得")
            # 履歴がある場合は、エージェントのメッセージリストに設定
            agent.messages = history_messages

        # エージェントを実行（常に現在のユーザー入力のみを渡す）
        response = await agent.invoke_async(user_input)

        result = response.message['content'][0]['text']

        # 会話をメモリに保存
        print("💾 学習内容をメモリに保存中...")
        save_conversation_to_memory(MEMORY_ID, actor_id, session_id, user_input, result)

        print(f"🤖 回答: {result[:100]}...")
        return result

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return f"申し訳ありません。エラーが発生しました: {str(e)}"

if __name__ == "__main__":
    app.run()
