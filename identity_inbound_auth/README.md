# AgentCore Identity (Inbound Auth)

* 下記のブログ記事のコードを参考にしています。
  - https://dev.classmethod.jp/articles/amazon-bedrock-agentcore-identity-cognito-azure-openai/


* AgentCore Identity のユースケース

1. Inbound Auth
    - AgentCore Runtime で動作する Agent の呼び出しに Bearer トークンが必要という構成にした場合、AgentCore Indetity を使用し、Bearer トークンを取得する
2. Outbound Auth
    1. AgentCore Identity を使用し Agent が外部サービスを呼び出すときと API キーを取得する
    2. AgentCore Identity を使用し Agent が AgentCore Gateway で外部サービスを呼び出すときとの Bearer トークンを取得する

## Inbound Auth
