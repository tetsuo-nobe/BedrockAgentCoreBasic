# マネジメントコンソールから Runtime に Agent をデプロイしてみる

* AgentCore が GA した後の 2026 年 1 月検証

* 事前準備不要でマネジメントコンソールからすぐにデプロイできる

## Agent のデプロイ手順

1. マネジメントコンソールにサインインして AgentCore のページに移動する

1. 左側のナビゲーションメニューで[エージェントランタイム]をクリックする

1. [ホストエージェント/ツール]をクリックする

1. [名前] を入力する

1. [エージェントソース] で [ソースタイプ] に [S3 ソース] を選択する

1. [S3 設定] で [テンプレートから始める] を選択する
   * これにより、テンプレートから Agent を自動作成できる

1. [保存先フォルダ] をデフォルトのままにする。
    * デフォルトのバケット名は、bedrock-agentcore-runtime-<AWSアカウントID>-<リージョンID>-<ユニークな値>
    * 自分で S3 バケットを選択することもできる

1. [テンプレートを選択] で [Strands agent] を選択する 

1. [許可] の [Amazon Bedrock AgentCore のサービスロール] で [新しいサービスロールを作成して使用] を選択する

1. その他はデフォルトのままにして、右下の [ホストエージェント/ツール] をクリックする

## デプロイした Agent を呼び出してみる

1. マネジメントコンソールのナビゲーションメニューで[エージェントランタイム] から [エージェント名] のリンクを選択する

1. [エンドポイント]セクションの[名前] が [DEFAULT] の左横のラジオボタンを選択する

1. [テストエンドポイント] をクリックする

1. [入力] で、下記のような JSON に変更する
   ```
   {"prompt": "こんにちは！"}
   ```
1. [実行] をクリックする

1. [出力] にエージェントからの回答が表示されることを確認する

## コードから呼び出す場合

1. マネジメントコンソールのナビゲーションメニューで[エージェントランタイム] から [エージェント名] のリンクを選択する

1. [呼び出しコードを表示] を展開表示する

1. [Python] のコードをコピーする

1. AWS アカウントで適切な権限を実行でき、boto3 が使用可能な開発環境でコピーした Python コードを保存する

1. コードを下記の内容で置き換える
    * 元のコードと違う箇所
      - secrets パッケージのインポート
      - session_id として 33 文字以上の文字列を生成
      - Agent 呼び出し時に session_id を指定
      - Agent 呼び出し時に qualifier の指定を削除

    ``` 
    import boto3
    import json
    import secrets

    client = boto3.client('bedrock-agentcore', region_name='ap-northeast-1')
    payload = json.dumps({"prompt": "生成 AI についてを分かりやすく説明して下さい。"})

    session_id = secrets.token_hex(17)

    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock-agentcore:ap-northeast-1:123456789012:runtime/hosted_agent_qfyms-i4HsycAHGS',
        runtimeSessionId=session_id,
        payload=payload
    )
    response_body = response['response'].read()
    response_data = json.loads(response_body)
    print("Agent Response:", response_data)se DEFAULT endpoint
    )
    ```

1. 呼び出しコードを実行する
