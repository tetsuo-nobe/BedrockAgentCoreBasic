# AgentCore Evaluation のオンデマンド評価のサンプル

## 前提条件と準備

* Python 3.10 以上

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

1. src フォルダの main.py をこのリポジトリの main.py の内容に書き換える

1. AWS リージョンを環境変数で指定する。(生成されたデフォルトの Agent のコードで使用しているため)
    - AgentCore Evaluation が使用できるリージョンを指定する

    ```
    export AWS_REGION=us-east-1
    ```

1. プロジェクトのフォルダに移動し、まずはローカルで実行する。（デフォルトポートは 8080 だが、使用されている場合は他のポートを使う）
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

1. デプロイされた Agent の動作確認として 下記を実行する

    ```
    agentcore invoke '{"prompt": "こんにちは！日本の首都はどこですか？"}'
    ```

    * agentcore create で作成した Strands Agent のコードをデフォルトのままデプロイした場合は、コンソールで表示される呼び出しコードは使用できない。
        - レスポンスの方式が違うため

    * Agent のコード (main.py) を変更した場合は、再度 `agentcore deploy` を実施すればよい


1. オンデマンド評価を行うため、セッション ID 用の UUID を作成

    ```
    SESSION_ID=$(uuidgen) 
    echo "セッションID: $SESSION_ID"
    ```

1. オンデマンド評価用に下記を実行する

    ```
    agentcore invoke '{"prompt": "Tokyoの天気をおしえてください"}' --session-id $SESSION_ID
    ```

    ```
    agentcore invoke '{"prompt": "new yorkの天気をおしえてください"}' --session-id $SESSION_ID
    ```

    ```
    agentcore invoke '{"prompt": "北海道の天気をおしえてください"}' --session-id $SESSION_ID
    ```

1. オンデマンド評価を実行
    - （1,2分待ってから実行する）

    ```
    agentcore eval run --session-id $SESSION_ID \
        --evaluator "Builtin.Helpfulness" \
        --evaluator "Builtin.GoalSuccessRate" \
        --evaluator "Builtin.Coherence" \
        --evaluator "Builtin.Faithfulness" \
        --evaluator "Builtin.ToolSelectionAccuracy"
    ```

1. 結果を確認する。
    - このリポジトリの result_example.txt に出力例がある

   
1. Agent のアンデプロイ
   ```
   agentcore destroy
   ```
