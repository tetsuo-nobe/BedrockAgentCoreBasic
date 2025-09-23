import asyncio
import anthropic
from bedrock_agentcore.identity.auth import requires_api_key

ANTHROPIC_API_KEY = None

# AgentCore Identity で登録した API KEY を取得
@requires_api_key(provider_name="ANTHROPIC_KEY")
async def need_api_key(*, api_key: str):
    global ANTHROPIC_API_KEY
    print("received api key for async func")
    ANTHROPIC_API_KEY = api_key

async def get_api_key():
    # APIキーを取得
    await need_api_key(api_key="")

# APIキーを非同期で取得
asyncio.run(get_api_key())
print(ANTHROPIC_API_KEY)

# SDK Client を作成
client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

# Claude の呼び出し
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[
        {
            "role": "user",
            "content": "こんにちは！"
        }
    ]
)
# 結果の出力
print(message.content[0].text)
