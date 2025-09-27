from email import contentmanager
import os
import boto3
# Agent と tool のインポート
from strands import Agent
from strands.models import BedrockModel
import logging
from dotenv import load_dotenv
from bedrock_agentcore.memory import MemoryClient

# logging の構成
logging.getLogger("strands").setLevel(logging.INFO) # より詳細なログを表示するにはDEBUGに設定する

# 環境変数読み込み
load_dotenv()

# グローバル設定
MEMORY_ID = os.getenv("MEMORY_ID")
REGION = os.getenv("REGION", "us-west-2")

# Memory Clientの初期化
memory_client = MemoryClient(region_name=REGION)

# 会話履歴を取得する関数
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

# 会話履歴を保存する関数
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

# Create an assistant agent
boto_session = boto3.Session(region_name="us-west-2")

bedrock_model = BedrockModel(
    model_id = "us.amazon.nova-lite-v1:0",
    temperature = 0.3,
    boto_session = boto_session
)

my_agent = Agent(
    model = bedrock_model,
    system_prompt = """あなたは優秀なアシスタントです。
    ユーザーからの問い合わせに丁寧に回答してください。"""
)

if __name__ == "__main__":
    actor_id = input("\nYour ID > ")
    session_id = input("\nSession ID > ")
    print("\n AI エージェントと会話しましょう！終了するには exit と入力してください。\n")
    
    # Run the agent in a loop for interactive conversation
    while True:
        user_input = input("\nYou > ")
        if user_input.lower() == "exit":
            print("Happy conversation!")
            break
        
        # 過去の会話履歴を取得
        print("📚 過去の会話履歴を取得中...")
        history_messages = load_conversation_history(MEMORY_ID, actor_id, session_id, max_results=10)

        if history_messages:
            print(f"✅ {len(history_messages)}件の過去メッセージを取得")
            # 履歴がある場合は、エージェントのメッセージリストに設定
            my_agent.messages = history_messages

        # エージェントを実行（常に現在のユーザー入力のみを渡す）
        response = my_agent(user_input)

        # 会話をメモリに保存
        print("💾 内容をメモリに保存中..." )
        save_conversation_to_memory(MEMORY_ID, actor_id, session_id, user_input, response.message["content"][0]["text"])

        # 回答を表示
        print(f"\nAgent > {response}")