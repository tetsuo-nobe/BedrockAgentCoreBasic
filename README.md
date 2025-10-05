# Amazon Bedrock AgentCore の基本的なサンプル

* AgentCore の各機能をシンプルに試すサンプル

## Browser
* browser_browser-use
    - Yahoo で検索を行う
* browser_playwright
    - 指定したURLにアクセスしてスクリーンショットを取得・保存する

## Code Interpreter
* code_interpreter
    - only_interpreter
        - Python の簡単なコードを実行
    - with_agent
        - Agent に指示した複数の値の平均値をコードを実行して求める

## Gateway
* gateway
    - Lambda 関数を Gateway により MCP のツールとして使用する
        - (このサンプルは、Identity の Outbound auth のサンプルでも使用する)

## Identity
* identity_inbound_auth
    - AgentCore Runtime にデプロイした Agent 使用時に Cognito で認証したトークンを必要とする
* identity_outbound_auth
    - 外部サービスにアクセス時に必要な API キーを取得する
    - AgentCore Runtime にデプロイした Agent から Gateway へアクセス時に必要なトークンを取得する

## Memory
* memory
    - long-term-memory
        - Agent との対話のサマリーを Long-term memory から取得する
    - short-term-memory
        - Agent との対話履歴を Short-term memory で管理する
    - tech-learning-assistant
        - Long-term memory を使用した技術学習アシスタント

## runtime
* Strands Agents の Agent を AgentCore Runtime でデプロイ

## runtime_mcp_server
* MCP Server を AgentCore Runtime でデプロイする

