from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType
import time

# Memory Clientの初期化
client = MemoryClient(region_name="us-west-2")

# 3つのストラテジーを定義
# それぞれに名前、説明、namespaceを設定
strategies = [
    {
        # セッションサマリー生成用ストラテジー
        StrategyType.SUMMARY.value: {
            "name": "SessionSummary",
            "description": "セッションの会話のサマリーを生成",
            "namespaces": ["myagent4long/summaries/{actorId}/{sessionId}"]
            # セッションごとにサマリーを作成
        }
    }
]

print("🚀 AgentCore Memory作成中...")
print("📝 設定内容:")
print(f"   - Summary Strategy: セッションごとのサマリー生成")

timestamp = int(time.time())
memory_name = f"AssistantLongMemory_{timestamp}"

# Memory作成（365日間のイベント保持）
memory = client.create_memory_and_wait(
    name=memory_name,
    strategies=strategies,
    description="アシスタント用のメモリ（ユーザー個別管理）",
)

memory_id = memory['id']
print(f"\n✅ Memory作成完了！")
print(f"   Memory ID: {memory_id}")
print(f"   Status: {memory['status']}")

# 各ストラテジーのIDを確認（自動生成される）
print(f"\n📋 生成されたStrategy IDs:")
for strategy in memory.get('strategies', []):
    print(f"   - {strategy['type']}: {strategy['strategyId']}")
    print(f"     Namespace: {strategy['namespaces'][0]}")

# .envファイルを自動で更新
with open('.env', 'r') as f:
    content = f.read()

updated_content = content.replace('MEMORY_ID=placeholder', f'MEMORY_ID={memory_id}')

with open('.env', 'w') as f:
    f.write(updated_content)

print(f"\n🎉 .envファイルを自動更新しました！")
