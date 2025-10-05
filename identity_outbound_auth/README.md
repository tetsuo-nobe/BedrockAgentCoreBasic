# AgentCore Identity (Outbound Auth)

## AgentCore Identity のユースケース

1. Inbound Auth
    - AgentCore Runtime で動作する Agent の呼び出しに Bearer トークンが必要という構成にする
2. Outbound Auth
    1. AgentCore Identity を使用し Agent が外部サービスを呼び出すときと API キーを取得する
    2. AgentCore Identity を使用し Agent が AgentCore Gateway で外部サービスを呼び出すときとの Bearer トークンを取得する

---
## Outbound Auth


### 1. AgentCore Identity を使用し Agent が外部サービスを呼び出すときと API キーを取得する

* **main-apiKey.py**
* サンプルコードでは Agent ではなく通常の Python コードから API キーを取得し、Anthropic SDK を使用して Claude を呼び出す

#### 準備

1. Anthropic の API キーを入手しておく

1. AWS マネジメントコンソールで AgentCore Identity の API キーを作成

1. Anthropic の SDK のインストール

    ```
    pip install anthropic
    ```
---

### ２. AgentCore Identity を使用し Agent が AgentCore Gateway で外部サービスを呼び出すときと API キーを取得する

* **main-bearerToken.py**
* サンプルコードでは Agent ではなく通常の Python コードから Bearer トークンを取得し、AgentCore Gateway で weather を呼び出す。
    - このリポジトリの gateway フォルダのサンプルで作成した weather を呼び出す前提
    - gateway サンプルでは Cognito から Bearer トークンを取得したが、このサンプルでは AgentCore Identity の機能を使用して Bearer トークン を取得する

#### 準備

1. AWS マネジメントコンソールで AgentCore Identity の OAuth クライアントを作成
    - カスタムプロバイダを選択して下記を入力 
        - AgentCore Gateway の Cognito ユーザープールの Client Id
        - AgentCore Gateway の Cognito ユーザープールの Client シークレッt 
        - AgentCore Gateway の Discovery URL
    - 作成した OAuth クライアントの名前をメモしておく

---

#### その他のサンプル

* **create-api-key.py**
    - コードから AgentCore Identity で管理するキーを作成するサンプル
* **test-anthropic.py**
    - スタンドアローンで Anthropic の API キーを使用するサンプル
---
* 参考にしたブログ記事
  - https://qiita.com/moritalous/items/6c822e68404e93d326a4


