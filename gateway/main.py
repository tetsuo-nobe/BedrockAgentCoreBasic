import base64
import os
import requests
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

def get_access_token():
    # 環境変数から値を取得
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    # discovery_url: Gatewayのページに表示されている。もしくは Cognito ページの [概要] で [トークン署名キー URL] として表示されている URL の末尾を /openid-configuration に変更したもの
    discovery_url = os.environ.get("DISCOVERY_URL")
    # カスタムスコープ:マネコンで Cognito のアプリケーションクライアントの [ログインページ] タブに表示されている
    custom_scope = os.environ.get("CUSTOM_SCOPE")
        
    if not all([client_id, client_secret, discovery_url, custom_scope]):
        raise ValueError(
            "必要な環境変数が設定されていません: CLIENT_ID, CLIENT_SECRET, DISCOVERY_URL, CUSTOM_SCOPE"
        )
    # Basic認証用のヘッダーを作成（base64エンコード）
    credentials = f"{client_id}:{client_secret}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    
    # ディスカバリーURLからトークンエンドポイントを取得
    discovery_response = requests.get(discovery_url)
    discovery_response.raise_for_status()
    discovery_data = discovery_response.json()
    token_endpoint = discovery_data["token_endpoint"]
    
    # アクセストークンを取得
    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}",
    }
    token_data = {"grant_type": "client_credentials", "scope": custom_scope}
    token_response = requests.post(
        token_endpoint, headers=token_headers, data=token_data
    )
    token_response.raise_for_status()
    token_json = token_response.json()
    access_token = token_json["access_token"]
    return access_token

access_token = get_access_token()
streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client(
        # AgentCore Gateway resource URL
        "https://gateway-20250920-9e5zferjbc.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp",
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
