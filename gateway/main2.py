import asyncio
import os

from bedrock_agentcore.identity.auth import requires_access_token
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient
from dotenv import load_dotenv

# .envファイルの内容を読み込む
load_dotenv()

# Gatewayのページに表示されている
gateway_url = os.environ.get("GATEWAY_URL")

# AgentCore Identity に事前作成した Cognito 用 OAuth2 Credential Provider の名前
# 事前に aws bedrock-agentcore-control create-oauth2-credential-provider で
# credentialProviderVendor: "CognitoOauth2" を指定して作成しておく必要がある
# (clientId / clientSecret はそのプロバイダー作成時に設定するため、
#  このスクリプト側では環境変数として持たなくなる)
provider_name = os.environ.get("PROVIDER_NAME")

# カスタムスコープ:マネコンで Cognito のアプリケーションクライアントの [ログインページ] タブに表示されている
custom_scope = os.environ.get("CUSTOM_SCOPE")

if not all([gateway_url, provider_name, custom_scope]):
    raise ValueError(
        "必要な環境変数が設定されていません: GATEWAY_URL, PROVIDER_NAME, CUSTOM_SCOPE"
    )


# requires_access_token が M2M (client_credentials) フローでアクセストークンを取得し、
# access_token 引数に注入してくれる。
# ローカル実行時は AgentCore Identity 側にワークロードIDが自動作成され、
# トークン取得・キャッシュもすべて AgentCore Identity 側で管理される。
@requires_access_token(
    provider_name=provider_name,
    scopes=[custom_scope],
    auth_flow="M2M",
)
async def run_agent(*, access_token: str):
    streamable_http_mcp_client = MCPClient(
        lambda: streamablehttp_client(
            # AgentCore Gateway resource URL
            gateway_url,
            headers={"Authorization": f"Bearer {access_token}"},
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


asyncio.run(run_agent())
