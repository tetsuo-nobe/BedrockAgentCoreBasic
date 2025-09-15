import sys

from bedrock_agentcore.tools.browser_client import BrowserClient
from playwright.sync_api import sync_playwright
from strands import Agent, tool
from strands.models import BedrockModel

region = "us-east-1"

# AgentCore Browser に Playwright で接続してスクリーンショットを取得するツール
@tool
def capture_page(url: str) -> str:
    """
    URLにアクセスし、スクリーンショットを取得します。A
    取得したスクリーンショットのファイルパスを返却します。
    """

    file_name = "image.png"

    # AgentCore BrowserClient の取得
    client = BrowserClient(region)
    client.start()

    # AgentCore Browser のエンドポイントと認証用ヘッダーを取得
    ws_url, headers = client.generate_ws_headers()

    # Playwright で接続
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(
            endpoint_url=ws_url, headers=headers
        )
        default_context = browser.contexts[0]
        page = default_context.pages[0]

        page = browser.new_page()
        page.goto(url)
        # スクリーンショットの取得
        page.screenshot(path=file_name)

        browser.close()

    client.stop()

    return file_name

# BedrockModel の作成
bedrock = BedrockModel(model_id="us.amazon.nova-lite-v1:0", region_name=region)

# Strands Agents のエージェントを作成
agent = Agent(model=bedrock, tools=[capture_page])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('使用方法: python main.py "プロンプト"')
        sys.exit(1)

    prompt = sys.argv[1]
    
    # StrandsAgent のエージェント実行
    agent(prompt)

