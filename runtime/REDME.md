# AgentCore Basic Examples

* https://docs.aws.amazon.com/bedrock-agentcore/

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

---
## Runtime

* Getting started with Amazon Bedrock AgentCore Runtime
    - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-getting-started.html
 
* ローカルで実行

    ```
    python my_agent.py
    ```

    ```
    curl -X POST http://localhost:8080/invocations \
    -H "Content-Type: application/json" \
    -d '{"prompt": "こんにちは！京都で有名な観光地を10箇所挙げてください。"}'
    ```

* Agent のデプロイ（Agent Runtime の作成）
  - 方法 1. boto3 で作成する場合
    - 作成した Agent のコンテナイメージをビルドしておく
    - ECR リポジトリを作成し、Agent のイメージを push しておく
    - boto3 の　bedrock-agentcore-control クライアントを作成し、create_agent_runtime で作成する
  
  - 方法 2. agentcore configure コマンドで作成する場合
    - プロジェクトフォルダを作成

    ```
    pip install bedrock-agentcore-starter-toolkit
    ```

    - ローカルモードで起動する場合もあるので、Docker を起動しておく

    - AgentCore Runtime が assume する role を作成しておく
        - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html
    
    ```
    agentcore configure --entrypoint my_agent.py -er arn:aws:iam::068048081706:role/my-AgentCore-runtime-role

    ```

   ```
   agentcore launch -l
   ```


    ```
    agentcore launch
    ```

    ```
    agentcore invoke '{"prompt": "こんにちは"}'
    ```
