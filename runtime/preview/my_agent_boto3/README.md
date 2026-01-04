# AgentCore Runtime

## 方法 1. boto3 で作成する場合

![boto3](images/Runtime-boto3.png)
    
1. 作成した Agent のコンテナイメージをビルドしておく
1. ECR リポジトリを作成し、Agent のイメージを push しておく
1. boto3 の　bedrock-agentcore-control クライアントを作成し、create_agent_runtime で作成する
