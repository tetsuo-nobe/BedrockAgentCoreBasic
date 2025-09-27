# AgentCore Memory を使用した技術学習アシスタントの作成

 * 下記のブログ記事の内容を試したものです。
    - [Amazon Bedrock AgentCore]Memory機能で会話履歴を記憶するエージェントを実装してみた](https://dev.classmethod.jp/articles/amazon-bedrock-agentcore-memory-sample-agent/)
    - ただし IAM ロールに設定するポリシーの内容は下記のように変更しています。
        - 変更前) bedrock:InvokeModel
        - 変更後) bedrock:InvokeModel* 
---
## 手順

1. パッケージのインストール
    - ```
      pip install -r requirements.txt
      ```

1. .env の MEMORY_ID の値は、placeholder にしておく(後で自動書き換えする際の前提条件となっているため)
    - ```
      # Memory設定（create_memory_and_wait.py または create_memory.pyが自動で更新）
      MEMORY_ID=placeholder
      ```

1. AgentCore Memory の長期メモリを作成(数分かかる)
    - ```
      python create_memory_and_wait.py
      ```
    - もしくは下記でも可能(下記の場合メモリ作成まで待機しない)
    - ```
      python create_memory.py
      ```
1. AgentCore Runtime で動作する Agent 用の IAM ロール作成
    - ```
      python create_iam_role.py
      ```
1. Agent を AgentCore Runtime でデプロイ
    - ```
      python deploy_agent.py
      ```
1. Chat アプリから Agent を呼び出し
    - ```
      python chat.py "Pythonプログラミングについて学習しようと思ってます。" \
        --user "userA" --session "test_session1"
      ```
    - ```
      python chat.py "ファイルのIO処理が苦手です。簡単な例を提示してください。" \
        --user "userA" --session "test_session1"
      ```
    - ```
      python chat.py "JavaScriptプログラミングについて学習しようと思ってます。" \
        --user "userB" --session "test_session1"
      ```
    - ```
      python chat.py "HelloWorldレベルのサンプルを提示してください。" \
        --user "userB" --session "test_session1"
      ```
    - ```
      python chat.py "私の苦手分野を教えてください" \
        --user "userA" 
      ```
    - ```
      python chat.py "私の学習進捗を教えてください" \
        --user "userB" 
      ```
---
## メモ

    - 参考ドキュメント:[Getting started with AgentCore Memory](https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/memory-getting-started.html)
    - ドキュメントでのメモリの作成方法の記述
        - 短期メモリの作成は create_memory
        - 長期メモリの作成は、create_memory_and_wait
            - この時ストラテジーの指定が必要
            - 長期メモリを作成すると短期メモリも使用でき、短期メモリの内容が非同期で抽出される
        - 短期メモリを作成する create_memory にストラテジーを指定して長期メモリを作成することも可能？
            - 元の記事ではそうしている
        - [この AWS Blog](https://aws.amazon.com/jp/blogs/news/introducing-amazon-bedrock-agentcore-securely-deploy-and-operate-ai-agents-at-any-scale/) では、短期メモリを create_memory_and_wait で作成している例もある?
        - **おそらく、create_memory_and_wait は、メモリ作成完了まで待機するというだけでしかない**
            - 長期メモリ作成には時間がかかるので、create_memory_and_wait を使うのではないか
            - **ストラテジーの記載の有無により、短期メモリ only か 長期メモリ付き短期メモリかが決まると思われる**
    - 短期メモリから長期メモリへは非同期で自動抽出される
        - [Long-term memory](https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/long-term-memory.html)
    - 短期メモリへの格納は create_event
    - 短期メモリからの取り出しは、list_events
    - 長期メモリからの取り出しは、retrieve_memories