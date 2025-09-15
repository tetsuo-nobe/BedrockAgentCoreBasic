from typing import Dict, Any
import os
import logging

from strands import Agent, tool
from strands.models import BedrockModel

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.tools.browser_client import BrowserClient
from browser_use import Agent as BrowserUseAgent
from browser_use.browser.session import BrowserSession as BU_BrowserSession
from browser_use.browser import BrowserProfile as BU_BrowserProfile
from langchain_aws import ChatBedrockConverse
from playwright._impl._errors import Error as PlaywrightError

import contextlib

# ログ設定（LOG_LEVEL 環境変数で制御: DEBUG/INFO/WARNING/ERROR）
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("browser_agent")

region = "us-east-1"
model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
#model_id="us.amazon.nova-lite-v1:0",


SYSTEM_PROMPT = """あなたはWeb自動化のアシスタントです。

原則:
1. ユーザーの指示を正確に読み取ってください
2. Web上の操作はrun_browser_taskツールを使って実行してください
3. 実施した操作と結果を簡潔に説明してください
4. CAPTCHAなど人間による検証が必要な場合は、次に取るべき行動を明示してください

ツールの使い方:
- 検索が必要な場合は、ユーザー入力から「短い検索語（名詞句）」を抽出してください。
- use_browserツールを呼び出す際、instruction引数には検索語のみを渡してください（例: 「スーパーマーケット」）。
- 説明文や敬語、語尾（〜を検索してください 等）は渡さないでください。
 - サイト内検索を行う場合は、ページ内の検索テキストボックスと検索ボタンを必ず使用し、アドレスバーや外部検索エンジンは使用しないでください。
 - 例: Yahoo! JAPANトップページ（https://www.yahoo.co.jp/）では、ページ内の検索ボックスに直接入力し、同ページの検索ボタンで検索を実行してください（外部検索は禁止）。

常に簡潔で有用な結果を返してください。
"""

# AgentCore Browser に browser-use で接続して Yahoo で検索を行うツール
@tool
async def run_browser_task(instruction: str, starting_page: str = "https://www.yahoo.co.jp/") -> str:
    """Execute web automation steps using AgentCore Browser and Browser-Use SDK.

    instruction: Natural language instruction (e.g., "macbookを検索して最初の商品の詳細を抽出してください").
    starting_page: Initial URL to open.
    """

    logger.info("use_browser start: starting_page=%s", starting_page)

    client = BrowserClient(region=region)
    bu_session = None
    try:
        client.start()
        ws_url, headers = client.generate_ws_headers()
        logger.info("browser session created (region=" + region + ")")
        logger.info("cdp ws_url: %s", ws_url[:100] + "..." if len(ws_url) > 100 else ws_url)

        profile = BU_BrowserProfile(
            headers=headers,
            timeout=180000,
        )
        bu_session = BU_BrowserSession(
            cdp_url=ws_url,
            browser_profile=profile,
        )

        logger.info("Starting browser session...")
        await bu_session.start()
        logger.info("Browser session started successfully")

        bedrock_chat = ChatBedrockConverse(
            model_id = model_id,
            region_name=region
        )

        query = instruction.strip() if instruction else "大阪城"
        task = (
            f"最初に、ブラウザツールの検索/URLバーに『{starting_page}』を入力してYahoo! JAPANトップへ移動してください。\n"
            f"次に、ページ内の検索テキストボックスに『{query}』と直接入力し、同ページの検索ボタンをクリックして検索を実行してください。\n"
            f"要件:\n"
            f"- 最初の遷移のみ、ブラウザツールの検索/URLバーを使用して {starting_page} に移動する\n"
            f"- 以降は外部検索エンジン（Yahoo! JAPAN等）やアドレスバー検索は使わない\n"
            f"- ページの検索ボックスと検索ボタンのみを使用\n"
            f"- ページの読み込み完了を待ってから操作\n"
            f"- 検索結果の上位を確認し、日本語で特徴を3点に要約\n"
        )

        browser_use_agent = BrowserUseAgent(
            task=task,
            llm=bedrock_chat,
            browser_session=bu_session,
        )

        logger.info("running Browser-Use task: %s", task[:100] + "...")

        result = await browser_use_agent.run()

        return result
    finally:
        if bu_session:
            with contextlib.suppress(Exception):
                await bu_session.close()
                logger.info("Browser session closed")
        with contextlib.suppress(Exception):
            client.stop()
            logger.info("Browser client stopped")


#async def browser_agent(payload: Dict[str, Any], context) -> Dict[str, Any]:
if __name__ == "__main__":
    """
    このコードのエントリポイント
    (Bedrock AgentCore Runtimeのエントリポイントにする場合は関数にしてcontextパラメータを受け取り、適切な形式でレスポンスを返す)
    """

    #user_input = payload.get("prompt", "")
    user_input = "「京都の観光名所」と検索して、その結果を要約して提示してください。"

    model = BedrockModel(
    model_id=model_id,
    params={"max_tokens": 2048, "temperature": 0.2},
    region=region,
    read_timeout=600,
    )


    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=[run_browser_task],
    )
    
    try:
        result = agent(user_input)
        print(f"エージェント応答: {result}")
        #return result
    
    except Exception as e:
        logger.error("Error in browser_agent: %s", str(e), exc_info=True)
        # エラーでも適切な形式で返す
        # return {
        #     "output": {
        #         "error": str(e),
        #         "instruction": user_input,
        #         "message": f"エラーが発生しました: {str(e)}"
        #     }
        # }


# if __name__ == "__main__":
#     app.run()