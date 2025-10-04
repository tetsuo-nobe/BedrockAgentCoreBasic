# AgentCore Gateway で Lambda 関数を MCP のツールとして使用する

* 下記のブログ記事のコードをベースにしています。
  - https://tech.nri-net.com/entry/implement_gateway_and_try_it_out

## 手順

1. ツールとして使用する AWS Lambda 関数の作成
    - lambda_function.py

1. AWS マネジメントコンソールで AgentCore Gateway を作成
    - 「Cognito を利用した設定のクイック作成 」 を選択
        - これにより Cognito の M2M タイプのユーザープールが自動的に作成される
    - ロールの自動作成を指定
        - ターゲットに指定する Lambda 関数を呼び出すポリシーが付与されたロールが自動作成される
    - ターゲットに作成した Lambda 関数の ARN を指定
    - ターゲットスキーマとして下記をインラインで指定
    - ```
      [
        {
            "description": "tool to get weather information for a specified location",
                "inputSchema": {
                "properties": {
                    "location": {
                    "description": "The location to get weather information for",
                    "type": "string"
                    }
                },
                "required": [
                    "location"
                ],
                "type": "object"
                },
                "name": "get_weather"
        }
      ]

1. AgentCore Gateway を作成すると、Cognitoユーザープールが作成されるので、以下の値をメモしておく
    - アプリケーションクライアント ID
    - クライアントシークレット
    - カスタムスコープ
        - マネコンのアプリケーションクライアントの [**ログインページ**] タブに表示されている
    - Discovery URL
        - マネコンで Gateway のページの [**Inbound Identity**] に表示されている
        - または Cognito のページの [**概要**] で [**トークン署名キー URL**] として表示されている URL の末尾を `/openid-configuration` に変更したもの

1. Strands Agents SDK を使用して Tool として呼び出す
    - モデルはデフォルトの Claude Sonnet 4 を使用。
    - Nova Lite でも試してみたが、うまく動作しなかった。
    - .env の内容
    - ```
      CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxx
      CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      DISCOVERY_URL=https://cognito-idp.us-west-2.amazonaws.com/us-west-2_xxxxxxxxx/.well-known/openid-configuration
      CUSTOM_SCOPE=xxxxxxxxxxxxxxxx/genesis-gateway:invoke
      ```
    
1. マネージメントコンソールで作成した AgentCore Gateway のページの **View invocation code** にも Gateway を使用してツールのリストを取得するコードの例が表示されている。
    - この例には、アプリクライアントやシークレット以外で、環境に応じた値（Gateway や Cognito の URL の値）が設定されているが、環境変数から取得するように変更した。
    - .env の内容
    - ```
      CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxx
      CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      TOKEN_URL=https://my-domain-xxxxxxxx.auth.us-west-2.amazoncognito.com/oauth2/token
      GATEWAY_URL=https://xxxxxxxxxxxxxxxxxxxx.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp
      ```

