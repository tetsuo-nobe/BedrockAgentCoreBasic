"""
Strands Agents + AgentCore Browser だけで Web 検索・要約を行うシンプル版。

- browser_use / LangChain は一切使用しない
- Strands 公式ツール strands_tools.browser の AgentCoreBrowser を利用する
  （LLM が init_session / navigate / クリック / テキスト抽出 / close などの
    ブラウザ操作を自律的に呼び出す。二重エージェント構成は不要）

必要なパッケージ:
    pip install strands-agents "strands-agents-tools[browser]" bedrock-agentcore
"""

import os
import logging

from strands import Agent
from strands.models import BedrockModel
from strands_tools.browser import AgentCoreBrowser

# ログ設定（LOG_LEVEL 環境変数で制御: DEBUG/INFO/WARNING/ERROR）
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("browser_agent")

region = "us-west-2"
# Claude Sonnet 4.6（4.6 世代はクロスリージョン推論プロファイル経由で指定する）
model_id = "us.anthropic.claude-sonnet-4-6"

# エージェントへの指示。ブラウザ操作は browser ツールで実行させる
SYSTEM_PROMPT = """あなたはWeb自動化のアシスタントです。

原則:
1. ユーザーの指示を正確に読み取ってください
2. Web上の操作は browser ツールを使って実行してください
3. 実施した操作と結果を簡潔に説明してください
4. CAPTCHAなど人間による検証が必要な場合は、次に取るべき行動を明示してください

検索の進め方（重要・効率優先）:
- ページ内の検索ボックスへの入力やボタンのクリックは行わないでください。
  代わりに、検索結果ページのURLへ navigate で直接移動してください。
- 検索には Bing を使います。次の形式でURLを組み立ててください:
    https://www.bing.com/search?q=<検索語をURLエンコードしたもの>
  例: 検索語が「京都 観光名所」なら
    https://www.bing.com/search?q=%E4%BA%AC%E9%83%BD%20%E8%A6%B3%E5%85%89%E5%90%8D%E6%89%80
- 検索語はユーザー入力から「短い名詞句」だけを抽出してください
  （敬語・語尾・「〜を検索して」などは含めない。例:「京都 観光名所」）
- Yahoo! JAPAN など特定サイトのトップページを経由しないでください。
  最初から Bing の検索結果URLへ直接移動します。

browser ツールの使い方（1操作ずつ呼び出す）:
1. init_session でセッションを開始する
2. 上記ルールで組み立てた Bing 検索結果URLへ navigate する
3. ページの読み込み完了を待つ
4. 検索結果ページのテキストを抽出し、上位の結果を確認する
5. 内容を日本語で3点に要約する
6. 最後に必ず close でセッションを閉じる

うまくいかない場合でも、別サイトを次々に試すのではなく、
同じ Bing 検索結果URLの再読み込みや検索語の調整で対応してください。

常に簡潔で有用な結果を返してください。
"""


def build_agent() -> Agent:
    """Strands Agent を構築して返す。"""
    model = BedrockModel(
        model_id=model_id,
        params={"max_tokens": 2048, "temperature": 0.2},
        region=region,
        read_timeout=600,
    )

    # AgentCore のマネージドブラウザをツールとして登録
    browser = AgentCoreBrowser(region=region)

    return Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=[browser.browser],
    )


if __name__ == "__main__":
    user_input = "「京都の観光名所」と検索して、その結果を要約して提示してください。"

    agent = build_agent()

    try:
        result = agent(user_input)
        print(f"エージェント応答: {result}")
    except Exception as e:
        logger.error("Error in browser_agent: %s", str(e), exc_info=True)
