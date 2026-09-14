# AgentCore CLI を使用した Agent のデプロイ

* 下記のドキュメントの手順に基づき実施
    - [Amazon Bedrock AgentCore の使用を開始する](https://docs.aws.amazon.com/ja_jp/bedrock-agentcore/latest/devguide/agentcore-get-started-cli.html)

## AgentCore CLI のインストール

* ワークで使用する開発環境で実施します。
* 今回使用する開発環境の権限の関係上、npm のグローバルパッケージ用ディレクトリを作成します。

    ```
    # ユーザー領域にグローバルパッケージ用ディレクトリを作成
    mkdir -p ~/.npm-global
    
    # npm のグローバルインストール先を変更
    npm config set prefix '~/.npm-global'
    
    # PATH に追加（bash の場合）
    echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
    source ~/.bashrc
    ```

* AgentCore CLI をインストールします。

    ```
    npm install -g @aws/agentcore
    ```

* AgentCore CLI のインストールを確認します。

    ```
    agentcore --version
    ```

    * バージョン番号が表示されることを確認します。

* Python でエージェントを作成するため、uv もインストールします。
    ```
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```


---
## Git リポジトリのクローン

* AgentCore CLI でデプロイするエージェントのコードや、デプロイした後に呼び出すコードを取得するため Git リポジトリをクローンします。

```
git clone https://github.com/tetsuo-nobe/BedrockAgentCoreBasic.git
```

* フォルダの移動

```
cd  ~/environment/BedrockAgentCoreBasic/runtime/agentcore-cli
```

---
## AgentCore プロジェクトの作成

* AgentCore CLI を使用する前に、使用するリージョンを設定します。

```
aws configure set region us-west-2
```

* いよいよ AgentCore CLI を使用します。
* まずは AgentCore Runtime でエージェントをデプロイするためのリソースを格納したプロジェクトフォルダを作成します。
* agentcore create コマンドを実行し、フォルダ名や、作成するリソース、デプロイ方法、使用する SDK、Memory の使用有無などを対話的に応答していきます。


```
agentcore create
```

* 対話モードで下記を選択
    - Project name: `handson` を **入力**
    - What would you like to build?: `Agent` を選択 
    - Agent name: `MyAgent` (デフォルト) を選択
    - Select agent type: `Create new agent` を選択
    - Language: `Python` を選択
    - Build: `Direct Code Deploy` を選択
    - Protocol: `HTTP` を選択
    - Framework: `Strands Agents SDK` を選択
    - Model: `Amazon Bedrock (us.anthropic.claude-sonnet-4-5-20250514-v1:0)` を選択
    - Memory: `None` を選択
    - Customiza advanced settings: (何も選択せず Enter)
    - 最後にもう一度 Enter

* プロジェクト作成が完了するまで少し待ち、完了後に下記でプロジェクトフォルダに移動します。
  
```
cd handson
```

---
## main.py の編集

* 開発環境の左側のナビゲーターで以下の main.py を開いて内容を確認します。
    - `BedrockAgentCoreBasic/runtime/agentcore-cli/main.py`
    - この　main.py がデプロイするエージェントのコードになります。
    - このコードでは、AgentCore のエンドポイントとして指定した関数から Strands Agents SDK のエージェントを呼び出しています。

* AgentCore プロジェクトで作成された main.py に上書きコピーします。

```
cp  ~/environment/BedrockAgentCoreBasic/runtime/agentcore-cli/main.py   ~/environment/BedrockAgentCoreBasic/runtime/agentcore-cli/handson/app/MyAgent/main.py
```
---

## AgentCore Runtime へのデプロイ

* デプロイするエージェントが完成したので、AgentCore Runtime へデプロイします。
* handson フォルダにいることを確認します。

```
pwd
```

* agentcore deploy コマンドでデプロイを実行します。

```
agentcore deploy
```

> [!NOTE]
> 途中、CDK の bootstrap 実行の確認が求められたら、Enter キーを押してください。

---
##  (オプション）マネジメントコンソールでのデプロイの確認

* マネジメントコンソールの検索で `agentcore` を入力して、AgentCore のページを表示します。
* 左側のナビゲーションメニューで [**構築**] - [**ランタイム**] をクリックします。
* [**ランタイムリソース**] に [**handson_MyAgent**] が表示され、[**ステータス**] が [**準備完了**] になっていることを確認します。

<img width="1417" height="809" alt="image" src="https://github.com/user-attachments/assets/e70ec4c9-2e87-452b-af4e-3ab208ea14bd" />


---

## AgentCore ラインタイムの ARN の取得

* デプロイしたエージェントを呼び出すためには、エージェントの Amazon Resource Name (ARN) が必要になるため、次のコマンドで取得します。

```
agentcore status
```

* 下記のような出力の中で ARN の値をメモしておきます。
    - 下記の例だと、**arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/handson_MyAgent-suHGqe9XiS**　が ARN の値になります。
```
Agents
  MyAgent: Deployed - Runtime: READY (arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/handson_MyAgent-suHGqe9XiS)
  URL: https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-west-2%3A123456789012%3Aruntime%2Fhandson_MyAgent-suHGqe9XiS/invocations
```



---
## デプロイしたエージェントの呼び出し

* エージェントを呼び出すコードを用意します。
* 下記のコマンドで、uv で実行するための準備を行います。

```
uv init --python 3.14
uv add "boto3[crt]==1.42.96"
```

* handson フォルダにいることを確認して下さい。

```
pwd
```

* エージェントを呼び出すコード (invoke.py) をリポジトリからコピーします。

```
cp ~/environment/BedrockAgentCoreBasic/runtime/agentcore-cli/invoke.py   ~/environment/BedrockAgentCoreBasic/runtime/agentcore-cli/handson/invoke.py
```

* invoke.py を編集して、デプロイしたエージェントの ARN をコードに設定します。

```
ARN=メモしたARN
```

```
sed -i "s|YOUR_AGENT_RUNTIME_ARN|$ARN|g" invoke.py
```

* ARN が正しく設定されていることを確認します。
    - `# ランタイム ARN を記載` というコメントがある行で、`agentRuntimeArn=` に ARN の値が設定されているか確認します。
```
cat invoke.py
```
 

* 呼び出しを実行します。

```
uv run invoke.py
```

* エージェントから回答が返ってくることを確認します。(下記は例です。）

```
こんにちは！😊

お元気ですか？何かお手伝いできることはあります
```

### お疲れさまでした！ 
#### AgentCore CLI を使用し、Strands Agents SDK で作成したエージェントを AgentCore ランタイムへデプロイして呼び出すことができました。

---

### （以下はオプションです。）

### クリーンアップ手順

* 作成した AgentCore ランタイムを削除する場合は、次の手順を実行します。

```
agentcore remove
```

   - `Agent` を選択
   - `MyAgent` を選択
   - 確認の Enter キーを押す

```
agentcore deploy
```

   - 確認の Enter キーを押す

* CDKTookit スタックの削除

```
aws cloudformation delete-stack --stack-name CDKToolkit
```

* ファイルの削除

```
cd ~
rm -rf ~/* ~/.[!.]* ~/..?*
```

* SSM セッションマネージャーを閉じ、マネジメントコンソールからサインアウトします。


---

## 環境のクリアについて
* (**講師が行います。**）
* CloudShell から下記を実行
    ```
    curl -L -o bedrock-s3-clear.sh https://tnobep-demo-public.s3.amazonaws.com/bedrock-s3-clear.sh && bash bedrock-s3-clear.sh us-west-2
    ```







-----------------------------------------------
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

    * agentcore create で作成した Strands Agent のコードをデフォルトのままデプロイした場合は、コンソールで表示される呼び出しコードは使用できない。
        - レスポンスの方式が違うため

1. Agent のコード (main.py) を変更した場合は、再度 `agentcore deploy` を実施すればよい
   
1. Agent のアンデプロイ
   ```
   agentcore destroy
   ```
