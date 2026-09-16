# AgentCore Identity (Inbound Auth)

* 参考ドキュメント
  - https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/runtime-oauth.html

---
## AgentCore Identity のユースケース

1. Inbound Auth
    1. AgentCore Runtime で動作する Agent の呼び出しに Bearer トークンが必要という構成にする
    2. AgentCore Gateway と統合したツールの呼び出し時に Bearer トークンが必要という構成にする

2. Outbound Auth
    1. AgentCore Identity を使用し Agent が外部サービスを呼び出すときに API キーを取得する
    2. AgentCore Identity を使用し Agent が外部サービスを呼び出すときに JWT トークンを取得する

---
### このワークは、BedrockAgentCoreBasic/prep/README.md の準備作業が完了し、AgentCore Runtime のワーク完了後に実施する想定です。
  - よって、 **Code Server 環境が構築され、当リポジトリが clone され、uv もインストールされ、agentcore CLI もインストールされている前提です。**

---
## 1. AgentCore Runtime で動作する Agent の呼び出しに Bearer トークンが必要という構成にする

![inbound](images/identity_in.png)

### ワークのタスク

* [タスク 1: agentcore CLI で Inbound 認証を構成したエージェントをデプロイする](#cli)
* [タスク 2: AWS マネジメントコンソール で Inbound 認証を構成したエージェントをデプロイする](#console)


---
<a id="cli"></a>
### タスク 1: agentcore CLI で Inbound 認証を構成したエージェントをデプロイする例

---
#### 環境へのアクセス

* 下記の URL をコピーして、ブラウザの新しいタブで開きます。
    - `https://d-9567586b55.awsapps.com/start`
* 講師が URL とユーザー ID やパスワードをご案内します。

* ご自身に割り当てられた sandbox 環境で AWS マネジメントコンソールへアクセスします。

1. AWS マネジメントコンソールで、**オレゴン (us-west-2) リージョン**に切り替えます。

---
#### 手順

* Code Server 環境を開き、ターミナルで下記のコマンドを実行します。

  * Cognito ユーザープールの作成と環境変数の設定を実行します。
    - ```
      cd  ~/environment/BedrockAgentCoreBasic/identity_inbound_auth
      ```

  * Cognito ユーザープールの作成と環境変数の設定を実行します。

    - ```
      chmod +x ./setup_cognito.sh
      ```

    - ```
      ./setup_cognito.sh
      ```
    - ```
      source cognito.env
      ```
    - 下記を実行し、DISCOVERY_URL と CLIENT_ID の値をメモしておきます。
    - ```
      echo DISCOVERY_URL = $DISCOVERY_URL
      echo CLIENT_ID = $CLIENT_ID
      ```

    - (参考）ユーザープールのクライアントでクライアントシークレットも作成する場合は、setup_cognito_with_secret.sh を参考にしてください。

  * Agent を Cognito のトークンによる認証が必要な構成で AgentCore Runtime にデプロイします。
    - エージェントのコードはリポジトリに用意されている `agent_exmple.py` です。
    
    - ```
      export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
      echo $AWS_ACCOUNT_ID
      ```
    - エージェントのプロジェクト作成
    - ```
      agentcore create \
        --name my_inbound_auth_agent \
        --project-name myInboundAuthAgent \
        --framework Strands \
        --model-provider Bedrock \
        --no-agent
      ```
    - プロジェクトフォルダへ移動
    - ```
      cd myInboundAuthAgent
      ```
   - エージェントのコードのコピー
    - ```
      cp  /home/ec2-user/environment/BedrockAgentCoreBasic/identity_inbound_auth/agent_example.py .
      ``` 
    - エージェントの追加（Inbound 認証を設定）
    - ``` 
      agentcore add agent \
        --name my_inbound_auth_agent \
        --type byo \
        --code-location . \
        --entrypoint agent_example.py \
        --language Python \
        --framework Strands \
        --model-provider Bedrock \
        --authorizer-type CUSTOM_JWT \
        --discovery-url "$DISCOVERY_URL" \
        --allowed-clients "$CLIENT_ID"
      ```
    - エージェントのデプロイ
    - ```
      agentcore deploy -y  -v
      ```

    - マネジメントコンソールでは、作成されたエージェントのインバウンド認証の設定は、「バージョン1」のリンクをクリックすることで確認できます。

    - agentcore launch 実行により出力される Agent ARN の値を環境変数に設定します。
        - Agent ARNに含まれる:（コロン）は%3Aに、 /（スラッシュ）は%2Fにエンコードする必要あり
    - 下記は例
    - arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my_inbound_auth_agent-4CpCfb8Ukn の場合
    - ```
      export ESCAPED_AGENT_ARN=arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A123456789012%3Aruntime%2Fmy_inbound_auth_agent-4CpCfb8Ukn 
      ```

---
#### 確認

*  Cognito で認証してトークンを取得

  - ```
    export TOKEN=$(aws cognito-idp initiate-auth \
      --client-id "$CLIENT_ID" \
      --auth-flow USER_PASSWORD_AUTH \
      --auth-parameters USERNAME='testuser',PASSWORD='PERMANENT_PASSWORD' \
      --region us-east-1 | jq -r '.AuthenticationResult.AccessToken')
    ```

*  Token を使用して呼び出し

  - ```
    export PAYLOAD='{"prompt": "こんにちは、 1+1の答えは?"}'
    export BEDROCK_AGENT_CORE_ENDPOINT_URL="https://bedrock-agentcore.us-west-2.amazonaws.com"

    curl -v -X POST "${BEDROCK_AGENT_CORE_ENDPOINT_URL}/runtimes/${ESCAPED_AGENT_ARN}/invocations?qualifier=DEFAULT" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}"
    ```

* 無効な Token の場合、エラーになることを確認

  - ```
    export TOKEN=xxx

    curl -v -X POST "${BEDROCK_AGENT_CORE_ENDPOINT_URL}/runtimes/${ESCAPED_AGENT_ARN}/invocations?qualifier=DEFAULT" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}"
    ```
---
* （オプション）環境のクリア
  - AgentCore のコンソールの「エージェントランタイム」からランタイムリソース: my_inbound_auth_agent を削除
  - Cognito のコンソールで「ユーザーエージェント」の MyUserPool を削除


---


<a id="console"></a>
### AWS マネジメントコンソール で Inbound 認証を構成したエージェントをデプロイする例

* ナビゲーションメニュー 「ラインタイムエージェント」からエージェントをデプロイする際に、「インバウンド認証」セクションで構成してエージェントをデプロイします。
    - 名前に「agent-pool-」という接頭辞がついた Cognito ユーザープールとそのアプリケーションクライアントが自動で作成されます。
    - このアプリケーションクライアントは、デフォルトでは **M2M タイプではありません。** よってクライアントシークレットもありません。

![inbound](images/agent-inbound-console.png)

* デプロイしたエージェントの「ランタイム ARN」の値を環境変数に設定します。
    - ARN に含まれる:（コロン）は%3Aに、 /（スラッシュ）は%2Fにエンコードする必要あり
    - 下記は例
    - arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my_inbound_auth_agent-4CpCfb8Ukn  の場合
    - ```
      export ESCAPED_AGENT_ARN=arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A123456789012%3Aruntime%2Fmy_inbound_auth_agent-4CpCfb8Ukn 
      ```

* またデプロイ後、Cognito ユーザープールとのクライアントが作成されているので、環境変数で POOL_ID にユーザープール ID を、CLIENT_ID に アプリケーションクライアント ID を設定します。

```
POOL_ID=us-east-1_IIvfidhXZ
CLIENT_ID=4k8bv0dda0aou82q0mhh2fec5
```

* Congnito ユーザープールにユーザーを作成します。

```
aws cognito-idp admin-create-user \
  --user-pool-id $POOL_ID \
  --username "testuser" \
  --temporary-password "Test@1234" \
  --region us-east-1 \
  --message-action SUPPRESS > /dev/null
```

```
aws cognito-idp admin-set-user-password \
  --user-pool-id $POOL_ID \
  --username "testuser" \
  --password "Demo@1234" \
  --region us-east-1 \
  --permanent > /dev/null
```

*  Cognito で認証してトークンを取得します。

```
export TOKEN=$(aws cognito-idp initiate-auth \
      --client-id "$CLIENT_ID" \
      --auth-flow USER_PASSWORD_AUTH \
      --auth-parameters USERNAME='testuser',PASSWORD='PERMANENT_PASSWORD' \
      --region us-east-1 | jq -r '.AuthenticationResult.AccessToken')
```

*  Token を使用して呼び出します。

```
export PAYLOAD='{"prompt": "こんにちは、 1+1の答えは?"}'
export BEDROCK_AGENT_CORE_ENDPOINT_URL="https://bedrock-agentcore.us-east-1.amazonaws.com"

curl -v -X POST "${BEDROCK_AGENT_CORE_ENDPOINT_URL}/runtimes/${ESCAPED_AGENT_ARN}/invocations?qualifier=DEFAULT" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}"
```

* 無効な Token の場合、エラーになることを確認します。

```
export TOKEN=xxx

curl -v -X POST "${BEDROCK_AGENT_CORE_ENDPOINT_URL}/runtimes/${ESCAPED_AGENT_ARN}/invocations?qualifier=DEFAULT" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}"
```

---

## 2. AgentCore Gateway と統合したツールの呼び出し時に Bearer トークンが必要という構成にする

### AgentCore Gateway 作成時に インバウンド認証を指定することで、この構成にできる。

![in2](images/identity_in2.png)

#### マネジメントコンソールで Cognito ユーザープールの同時作成または既存ユーザープールの選択も可能

* 同時に作成するオプションを選択した場合、名前に「my-user-pool-」という接頭辞がついた Cognito ユーザープールとそのアプリケーションクライアントが自動作成される。
    - このアプリケーションクライアントは、**M2M タイプ** であり、クライアントシークレットが設定されている

* 手順は、[AgentCore Gateway で Lambda 関数を MCP のツールとして使用する](https://github.com/tetsuo-nobe/BedrockAgentCoreBasic/tree/main/gateway) に掲載

