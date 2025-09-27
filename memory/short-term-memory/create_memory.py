from bedrock_agentcore.memory import MemoryClient
import time

# Memory Clientの初期化
client = MemoryClient(region_name="us-west-2")

print("🚀 AgentCore Memory作成中...")

timestamp = int(time.time())
memory_name = f"AssistantMemory_{timestamp}"

# Memory作成（365日間のイベント保持）
memory = client.create_memory(
    name=memory_name,
    description="エージェント用のメモリ（ユーザー個別管理）",
)

memory_id = memory['id']
print(f"\n✅ Memory作成完了！")
print(f"   Memory ID: {memory_id}")
print(f"   Status: {memory['status']}")

# .envファイルを自動で更新
with open('.env', 'r') as f:
    content = f.read()

updated_content = content.replace('MEMORY_ID=placeholder', f'MEMORY_ID={memory_id}')

with open('.env', 'w') as f:
    f.write(updated_content)

print(f"\n🎉 .envファイルを自動更新しました！")
