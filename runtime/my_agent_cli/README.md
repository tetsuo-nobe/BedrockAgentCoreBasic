# AgentCore Runtime

## 方法 3. agentcore configure コマンドで作成する場合
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
S