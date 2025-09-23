# AgentCore Identity を使用せず、.env で API KEY を取得する場合のサンプル
import anthropic
import os
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

# API KEY の取得
my_api_key = os.environ.get("ANTHROPIC_API_KEY") 

# APIキーを直接指定
client = anthropic.Anthropic(
    api_key=my_api_key
)

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
print(message.content[0].text)