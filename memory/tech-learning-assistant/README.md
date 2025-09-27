# AgentCore Memory を使用した技術学習アシスタントの作成

 * 下記のブログ記事の内容を試したものです。
    - [Amazon Bedrock AgentCore]Memory機能で会話履歴を記憶するエージェントを実装してみた](https://dev.classmethod.jp/articles/amazon-bedrock-agentcore-memory-sample-agent/)
    - ただし IAM ロールに設定するポリシーの内容は下記のように変更しています。
        - 変更前) bedrock:InvokeModel
        - 変更後) bedrock:InvokeModel* 

* メモ
    - 参考ドキュメント:[Getting started with AgentCore Memory](https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/memory-getting-started.html)
    - ドキュメントでのメモリの作成方法の記述
        - 短期メモリの作成は create_memory
        - 長期メモリの作成は、create_memory_and_wait
            - この時ストラテジーの指定が必要
            - 長期メモリを作成すると短期メモリも使用でき、短期メモリの内容が非同期で抽出される
        - 短期メモリを作成する create_memory にストラテジーを指定して長期メモリを作成することも可能？
            - このコードではそうしている
        - [この AWS Blog](https://aws.amazon.com/jp/blogs/news/introducing-amazon-bedrock-agentcore-securely-deploy-and-operate-ai-agents-at-any-scale/) では、短期メモリを create_memory_and_wait で作成している例もある?
        - **おそらく、create_memory_and_wait は、メモリ作成完了まで待機するというだけでしかない**
            - 長期メモリ作成には時間がかかるので、create_memory_and_wait を使うのではないか
            - **ストラテジーの記載の有無により、短期メモリ only か 長期メモリ付き短期メモリかが決まると思われる**
    - 短期メモリから長期メモリへは非同期で自動抽出される
        - [Long-term memory](https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/long-term-memory.html)
    - 短期メモリへの格納は create_event
    - 短期メモリからの取り出しは、list_events
    - 長期メモリからの取り出しは、retrieve_memories