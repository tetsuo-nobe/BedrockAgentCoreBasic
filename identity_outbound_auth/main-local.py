import base64
import os
import requests
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
from dotenv import load_dotenv
from bedrock_agentcore.identity.auth import requires_access_token

# .envファイルの内容を読み込見込む
load_dotenv()

ACCESS_TOKEN = None

# 環境変数から値を取得
provider_name = os.environ.get("PROVIDER_NAME") # AgentCore Identityの Name
# カスタムスコープ:マネコンで Cognito のアプリケーションクライアントの [ログインページ] タブに表示されている
custom_scope = os.environ.get("CUSTOM_SCOPE")
# Gatewayのページに表示されている
gateway_url = os.environ.get("GATEWAY_URL") 

@requires_access_token(
    provider_name=provider_name, 
    scopes=[custom_scope], 
    auth_flow="M2M",
)
    
async def need_access_token(*, access_token: str):
    global ACCESS_TOKEN
    print("received api key for async func")
    ACCESS_TOKEN = access_token

async def get_token():
    # APIキーを取得
    await need_access_token(access_token="")

# APIキーを非同期で取得
asyncio.run(get_token())
print(ACCESS_TOKEN)

streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client(
        # AgentCore Gateway resource URL
        gateway_url,
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
)
with streamable_http_mcp_client:
    tools = streamable_http_mcp_client.list_tools_sync()
    
    # デフォルトの Claude Sonnet 4 ではなく Nova Lite を使用しようとしたがうまくいかなかった。
    # BedrockModel の作成
    # bedrock = BedrockModel(model_id="us.amazon.nova-lite-v1:0", region_name="us-west-2")
    # agent = Agent(tools=tools, model=bedrock )
    # デフォルトの Claude Sonnet 4 であれば動作した。
    agent = Agent(tools=tools)
    agent("東京の天気を教えてください。")
