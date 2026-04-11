import os
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from typing import List, Dict

# AgentCore Runtime ARN
AGENTCORE_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/ppt_convert_server-3HP48F2nRh"

def create_stdio_mcp_client(command: str, args: List[str], env: Dict) -> MCPClient:
    """stdio MCPクライアントを作成する関数"""
    stdio_mcp_client = MCPClient(
        lambda: stdio_client(StdioServerParameters(command=command, args=args, env=env)),
        startup_timeout=60
    )
    return stdio_mcp_client

def create_aws_iam_streamable_http_mcp_client(
    url: str,
    aws_service: str = "bedrock-agentcore"
) -> MCPClient:
    """MCP Proxy for AWSを利用したMCPクライアントを作成する関数"""
    streamable_http_mcp_client = MCPClient(
        lambda: aws_iam_streamablehttp_client(
            endpoint=url,
            aws_service=aws_service,
            aws_region="us-west-2",
        )
    )
    return streamable_http_mcp_client

def get_mcp_endpoint() -> str:
    encoded_arn = AGENTCORE_RUNTIME_ARN.replace(":", "%3A").replace("/", "%2F")
    return f"https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"

prompt = """
DynamoDBのtech-reportテーブルから最新の技術レポートを取得して、それをPPT形式に変換してください。
完了後は変換したファイルを取得するURLをユーザーへ明示してください。
"""

def main():
    mcp_endpoint = get_mcp_endpoint()
    print(mcp_endpoint)
    gateway_server_client= create_aws_iam_streamable_http_mcp_client(mcp_endpoint) 
    aws_mcp_client = create_stdio_mcp_client(
        command="uvx",
        args=[
            "mcp-proxy-for-aws@1.1.5",
            "https://aws-mcp.us-east-1.api.aws/mcp",
            "--metadata", "AWS_REGION=us-west-2"
        ],
        env={
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY":os.getenv("AWS_SECRET_ACCESS_KEY"),
        }
    )
    with gateway_server_client, aws_mcp_client:
        tools = gateway_server_client.list_tools_sync()
        tools.extend(aws_mcp_client.list_tools_sync())
        # Bedrockのモデルを定義
        model = BedrockModel(model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0")
        # エージェントを初期化
        agent = Agent(
            model=model,
            tools=tools
        )
        agent(prompt)

if __name__ == "__main__":
    main()
