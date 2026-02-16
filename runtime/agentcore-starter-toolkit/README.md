# AgentCore Starter Toolkit を使用した Agent のデプロイ

* 下記のドキュメントの手順に基づき実施
    - [Get started with Amazon Bedrock AgentCore](https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/agentcore-get-started-toolkit.html)

## 前提条件と準備

* Python 3.10 以上
* ドキュメントには記載がないが、uv もインストールしておくのが良い。
  - （agentcore dev コマンドでローカルでの実行時に使用されるため）
    ```
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

* AgentCore Starter Toolkit がインストールされていること
    - ```
      pip install bedrock-agentcore-starter-toolkit
      ```

## 手順

1.  AgentCore プロジェクトの作成。下記のコマンド実行後、対話的に使用する Agent の SDK などを指定していく 

    ```
    agentcore create
    ```

    - .bedrock_agentcore.yaml も生成される。これはデプロイ時に必要になる。

1. AWS リージョンを環境変数で指定する。(生成されたデフォルトの Agent のコードで使用しているため)

    ```
    export AWS_REGION=ap-northeast-1
    ```

1. まずはローカルで実行する。（デフォルトポートは 8080 だが、使用されている場合は他のポートを使う）
    ```
    agentcore dev
    ```
1. 下記コマンドにより、ローカル実行されている Agent を呼び出せる

    ```
    agentcore invoke --dev "Hello!"
    ```

    * ポートを指定する場合は下記
    ```
    agentcore invoke --dev "こんにちは!" --port 8081
    ```

1. 下記により AgentCore Runtme にデプロイする

    ```
    agentcore deploy
    ```
1. 下記により Agentを呼び出す

    ```
    agentcore invoke '{"prompt": "tell me a joke"}'
    ```

    ```
    agentcore invoke '{"prompt": "こんにちは！日本の首都はどこですか？"}'
    ```
1. Agent のコード (main.py) を変更した場合は、再度 `agentcore deploy` を実施すればよい
   
* agentcore create で作成した Strands Agent のコードをデフォルトのままデプロイした場合は、コンソールで表示される呼び出しコードは使用できない。
    - レスポンスの方式が違うため

1. Agent のアンデプロイ
   ```
   agentcore destroy
   ```
