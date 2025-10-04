# AgentCore Runtime

## 方法 1. boto3 で作成する場合
    - 作成した Agent のコンテナイメージをビルドしておく
    - ECR リポジトリを作成し、Agent のイメージを push しておく
    - boto3 の　bedrock-agentcore-control クライアントを作成し、create_agent_runtime で作成する
