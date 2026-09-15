"""
AgentCore Gateway のセマンティック検索を試すサンプルコード

Gateway 作成時にセマンティック検索を有効化していると、組み込みツール
`x_amz_bedrock_agentcore_search` が利用できる。
自然言語のクエリを渡すと、Gateway に登録された多数のツールの中から
description の意味的な類似度で関連ツールだけを動的に絞り込んで返してくれる。

前提:
- Gateway 作成時にセマンティック検索を有効化していること
- .env に GATEWAY_URL / CLIENT_ID / CLIENT_SECRET / DISCOVERY_URL / CUSTOM_SCOPE を設定していること
- 登録済みターゲット(ツール)の toolSchema に description が設定されていること
  (検索は description の意味でマッチするため必須)

実行:
    python semantic_search.py "東京の天気を調べたい"
    # 引数を省略すると既定のクエリで検索する
"""

import base64
import json
import os
import sys

import requests
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient
from dotenv import load_dotenv

# セマンティック検索用の組み込みツール名
SEARCH_TOOL_NAME = "x_amz_bedrock_agentcore_search"

# .env ファイルの内容を読み込む
load_dotenv()

# Gateway のページに表示されている URL
gateway_url = os.environ.get("GATEWAY_URL")


def get_access_token():
    """Cognito の client_credentials フローでアクセストークンを取得する。"""
    # 環境変数から値を取得
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    # discovery_url: Gateway のページに表示されている。もしくは Cognito ページの
    # [概要] で [トークン署名キー URL] として表示されている URL の末尾を
    # /openid-configuration に変更したもの
    discovery_url = os.environ.get("DISCOVERY_URL")
    # カスタムスコープ: マネコンで Cognito のアプリケーションクライアントの
    # [ログインページ] タブに表示されている
    custom_scope = os.environ.get("CUSTOM_SCOPE")

    if not all([client_id, client_secret, discovery_url, custom_scope]):
        raise ValueError(
            "必要な環境変数が設定されていません: "
            "CLIENT_ID, CLIENT_SECRET, DISCOVERY_URL, CUSTOM_SCOPE"
        )

    # Basic 認証用のヘッダーを作成（base64 エンコード）
    credentials = f"{client_id}:{client_secret}"
    auth_header = base64.b64encode(credentials.encode()).decode()

    # ディスカバリー URL からトークンエンドポイントを取得
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


def extract_text_from_result(call_result):
    """MCPClient.call_tool_sync の戻り値からテキスト部分を取り出す。

    戻り値は {"content": [{"text": ...}, ...]} のような形式になっているため、
    text フィールドを結合して返す。
    """
    texts = []
    content = call_result.get("content", []) if isinstance(call_result, dict) else []
    for block in content:
        # dict / オブジェクトどちらの形式でも text を拾えるようにする
        if isinstance(block, dict):
            text = block.get("text")
        else:
            text = getattr(block, "text", None)
        if text:
            texts.append(text)
    return "\n".join(texts)


def main():
    # コマンドライン引数があればそれを検索クエリにする。なければ既定値。
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "東京の天気を調べたい"

    if not gateway_url:
        raise ValueError("環境変数 GATEWAY_URL が設定されていません")

    access_token = get_access_token()
    streamable_http_mcp_client = MCPClient(
        lambda: streamablehttp_client(
            # AgentCore Gateway resource URL
            gateway_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    )

    with streamable_http_mcp_client:
        # まず Gateway から見えるツール一覧を確認する。
        # セマンティック検索が有効なら、この一覧に
        # x_amz_bedrock_agentcore_search が含まれる。
        tools = streamable_http_mcp_client.list_tools_sync()
        tool_names = [tool.tool_name for tool in tools]

        print("=== Gateway から見えるツール一覧 ===")
        for name in tool_names:
            print("-", name)
        print(f"合計 {len(tools)} 個のツール\n")

        if SEARCH_TOOL_NAME not in tool_names:
            print(
                f"[警告] セマンティック検索ツール '{SEARCH_TOOL_NAME}' が見つかりません。\n"
                "Gateway 作成時にセマンティック検索を有効化しているか確認してください。"
            )
            return

        # セマンティック検索を実行する。
        # 組み込みツール x_amz_bedrock_agentcore_search に自然言語クエリを渡すと、
        # 関連するツールだけが動的に絞り込まれて返る。
        print(f"=== セマンティック検索を実行: query='{query}' ===")
        search_result = streamable_http_mcp_client.call_tool_sync(
            tool_use_id="semantic-search-1",
            name=SEARCH_TOOL_NAME,
            arguments={"query": query},
        )

        # 検索結果を見やすく表示する
        result_text = extract_text_from_result(search_result)
        if result_text:
            # JSON として整形できるなら整形して表示する
            try:
                parsed = json.loads(result_text)
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
            except (json.JSONDecodeError, TypeError):
                print(result_text)
        else:
            # 想定外の形式の場合は生の戻り値をそのまま表示する
            print(search_result)


if __name__ == "__main__":
    main()
