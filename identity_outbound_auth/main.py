"""
AgentCore Runtime用のエージェント実装例
Outbound認証を使用してGatewayを呼び出す

必要な環境変数:
- PROVIDER_NAME: AgentCore Identityのクレデンシャルプロバイダー名
- CUSTOM_SCOPE: OAuth2スコープ（例: gateway-resource-server/read）
- GATEWAY_URL: AgentCore GatewayのURL
"""

import os
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.models import BedrockModel
from bedrock_agentcore.identity.auth import requires_access_token
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# 環境変数から設定を取得
PROVIDER_NAME = os.environ.get("PROVIDER_NAME", "resource-provider-oauth-client-pasa8")
CUSTOM_SCOPE = os.environ.get("CUSTOM_SCOPE", "get-weather-gw/genesis-gateway:invoke")
GATEWAY_URL = os.environ.get("GATEWAY_URL", "https://get-weather-gw-8risf7vrf6.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp")

# BedrockAgentCoreAppのインスタンスを作成
app = BedrockAgentCoreApp()


@requires_access_token(
    provider_name=PROVIDER_NAME,
    scopes=[CUSTOM_SCOPE],
    auth_flow="M2M",  # Machine-to-Machine認証
)
async def invoke_agent_with_gateway(user_message: str, *, access_token: str):
    """
    Outbound認証を使用してGatewayを呼び出し、エージェントを実行
    
    Args:
        user_message: ユーザーからの入力メッセージ
        access_token: AgentCore Identityから自動取得されるアクセストークン
    
    Returns:
        str: エージェントの応答
    """
    print(f"[INFO] Access token obtained: {access_token[:30]}...")
    print(f"[INFO] Gateway URL: {GATEWAY_URL}")
    print(f"[INFO] User message: {user_message}")
    
    # Gatewayへのアクセス用のHTTPトランスポートを作成
    def create_http_transport(headers=None):
        """Authorization headerを含むHTTPトランスポートを作成"""
        headers = {**headers} if headers else {}
        headers["Authorization"] = f"Bearer {access_token}"
        return streamablehttp_client(GATEWAY_URL, headers=headers)
    
    # MCPクライアントを作成
    mcp_client = MCPClient(create_http_transport)
    
    try:
        # MCPクライアントを使用してGatewayからツールを取得
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            print(f"[INFO] Available tools from Gateway: {len(tools)}")
            
            # Bedrockモデルを作成
            bedrock_model = BedrockModel(
                inference_profile_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
                temperature=0.0,
                streaming=True
            )
            
            # Strands Agentを作成
            agent = Agent(
                model=bedrock_model,
                tools=tools
            )
            
            # エージェントを実行
            print(f"[INFO] Invoking agent...")
            response = agent(user_message)
            print(f"[INFO] Agent response received")
            
            return str(response)
    
    except Exception as e:
        error_msg = f"Error invoking agent: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise


@app.entrypoint
async def invoke(payload, context):
    """
    AgentCore Runtimeのエントリーポイント
    
    Args:
        payload: リクエストペイロード（{"prompt": "user message"}）
        context: リクエストコンテキスト（session_id等を含む）
    
    Returns:
        dict: レスポンス（{"result": "agent response"}）
    """
    # ペイロードからユーザーメッセージを取得
    user_message = payload.get("prompt", "Hello, how can you help me?")
    
    print(f"[INFO] ===== New Invocation =====")
    print(f"[INFO] Session ID: {context.session_id}")
    print(f"[INFO] User prompt: {user_message}")
    
    try:
        # Outbound認証を使用してエージェントを実行
        response = await invoke_agent_with_gateway(
            user_message=user_message,
            access_token=""  # @requires_access_tokenが自動的にトークンを注入
        )
        
        print(f"[INFO] Invocation completed successfully")
        
        return {
            "result": response,
            "session_id": context.session_id
        }
    
    except Exception as e:
        error_msg = f"Invocation failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        
        return {
            "error": error_msg,
            "session_id": context.session_id
        }


if __name__ == "__main__":
    # AgentCore Runtimeで実行
    app.run()
