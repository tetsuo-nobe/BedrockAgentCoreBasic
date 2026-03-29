# uv のプロジェクトからエージェントのファイルだけで AgentCore Runtime へデプロイ

* (agentcore create を使用しないパターン)

1. uv のインストール

    ```
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    ```
    uv --version
    ```


1. uv でプロジェクト作成  

    ```
    AGENT_NAME=myagent
    uv init ${AGENT_NAME} --python 3.13
    ```

1. **作成したプロジェクトの main.py を削除する**

1. プロジェクトにパッケージをインストール

    ```
    cd ${AGENT_NAME}
    uv add mcp==1.25.0  strands-agents==1.20.0 nest-asyncio==1.6.0 streamlit==1.52.2
    ```

1. プロジェクトにパッケージをインストール

    ```
    cd ${AGENT_NAME}
    uv add mcp==1.25.0  strands-agents==1.20.0 nest-asyncio==1.6.0 bedrock-agentcore-starter-toolkit==0.2.5
    ```

1. エージェントのコードを作成
    * agent.py

1. エージェントを AgentCore Runtime へデプロイするための構成

    ```
    AGENT_NAME=agent.py
    uv run agentcore configure -e ${AGENT_NAME} --region us-west-2
    ```
    - Agent name
    - Deployment Configuration (Direct Code Deploy or Container)
    - Execution Role (auto-create)
    - ECR Repository (auto-create)
    - Authorization Configuration (no)
    - Request Header Allowlist (no)
    - Memory Configuration (Type 's' to skip )

1. エージェントを AgentCore Runtime へデプロイ

    ```
    uv run agentcore deploy
    ```

1. コマンドで呼出し

    ```
    uv run agentcore invoke '{"prompt": "こんにちは！"}'     
    ```

1. コードから呼出し

    ```
    python3 agent_client.py   
    ```
