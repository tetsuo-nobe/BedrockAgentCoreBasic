# AgentCore Identity (Inbound Auth)

* 下記のドキュメントを参考にしています。
  - https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/runtime-oauth.html

* AgentCore Identity のユースケース

1. Inbound Auth
    - AgentCore Runtime で動作する Agent の呼び出しに Bearer トークンが必要という構成にする
2. Outbound Auth
    1. AgentCore Identity を使用し Agent が外部サービスを呼び出すときと API キーを取得する
    2. AgentCore Identity を使用し Agent が AgentCore Gateway で外部サービスを呼び出すときとの Bearer トークンを取得する

## Inbound Auth

  * Agent を Cognito のトークンによる認証が必要な構成で AgentCore Runtime にデプロイ
    - ```
      agentcore configure --entrypoint agent_example.py \
        --name hello_agent \
        --execution-role arn:aws:iam::068048081706:role/my-AgentCore-runtime-role \
        --disable-otel \
        --requirements-file requirements.txt \
        --authorizer-config "{\"customJWTAuthorizer\":{\"discoveryUrl\":\"$DISCOVERY_URL\",\"allowedClients\":[\"$CLIENT_ID\"]}}"
      ```

    - ```
      agentcore launch
      ```

*  Cognito で認証してトークンを取得

  - ```
    export TOKEN=$(aws cognito-idp initiate-auth \
      --client-id "$CLIENT_ID" \
      --auth-flow USER_PASSWORD_AUTH \
      --auth-parameters USERNAME='testuser',PASSWORD='PERMANENT_PASSWORD' \
      --region us-east-1 | jq -r '.AuthenticationResult.AccessToken')
    ```

*  OAuth token を使用して呼び出し

  - Agent ARNに含まれる:（コロン）は%3Aに、 /（スラッシュ）は%2Fにエンコードする必要あり

  - ```
    export PAYLOAD='{"prompt": "こんにちは、 1+1の答えは?"}'
    export BEDROCK_AGENT_CORE_ENDPOINT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com"
    export ESCAPED_AGENT_ARN=arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A068048081706%3Aruntime%2Fhello_agent-I5Xah3DF7J

    curl -v -X POST "${BEDROCK_AGENT_CORE_ENDPOINT_URL}/runtimes/${ESCAPED_AGENT_ARN}/invocations?qualifier=DEFAULT" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d ${PAYLOAD}
    ```

