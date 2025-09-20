import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import os
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TOKEN_URL = os.environ.get("TOKEN_URL")
GATEWAY_URL = os.environ.get("GATEWAY_URL")


def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )

  return response.json()['access_token']

async def execute_mcp(
    url,
    headers=None
):
    headers = {**headers} if headers else {}
    async with streamablehttp_client(
       url=url,
       headers=headers,
    ) as (
        read_stream,
        write_stream,
        callA,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            # 1. Perform initialization handshake
            print("Initializing MCP...")
            _init_response = await session.initialize()
            print(f"MCP Server Initialize successful! - {_init_response}")

            # 2. List available tools
            print("Listing tools...")
            cursor = True
            tools = []
            while cursor:
                next_cursor = cursor
                if type(cursor) == bool:
                    next_cursor = None
                list_tools_response = await session.list_tools(next_cursor)
                tools.extend(list_tools_response.tools)
                cursor = list_tools_response.nextCursor

            tool_names = []
            if tools:
                for tool in tools:
                    tool_names.append(tool.name)
            tool_names_string = "\n".join(tool_names)
            print(
                f"List MCP tools. # of tools - {len(tools)}"
               f"List of tools - \n{tool_names_string}\n"
            )

# Example usage
gateway_url = GATEWAY_URL
access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
headers = {
    "Authorization": f"Bearer {access_token}"
}
asyncio.run(execute_mcp(url=gateway_url, headers=headers))