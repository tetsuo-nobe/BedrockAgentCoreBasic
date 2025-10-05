# AgentCore Runtime

* https://docs.aws.amazon.com/bedrock-agentcore/

---

## 準備

* 前提
    - ポート 8080 を利用できること
    - Python 3.11 以降の Runtime を利用できること
    - ARM64 Machine で Docker が利用できること

* bedrock-agentcore パッケージのインストール

    ```
    pip install bedrock-agentcore
    ```

* Strands Agents のパッケージのインストール

    ```
    pip install strands-agents
    pip install strands-agents-tools
    ```

* Agent をローカルで実行

    ```
    python my_agent.py
    ```

    ```
    curl -X POST http://localhost:8080/invocations \
    -H "Content-Type: application/json" \
    -d '{"prompt": "こんにちは！京都で有名な観光地を10箇所挙げてください。"}'
    ```

---
## AgentCore Runtime にエージェントをデプロイ

* Getting started with Amazon Bedrock AgentCore Runtime
    - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-getting-started.html
 

* Agent のデプロイ（Agent Runtime の作成）
  - 方法 1. boto3 で作成する
    - my_agent_boto3 フォルダ

  - 方法 2. bedrock_agentcore_starter_toolkit で作成する
    - my_agent_toolkit フォルダ

  - 方法 3. agentcore configure コマンドで作成する
    - my_agent_cli フォルダ
