# AgentCore Identity (Outbound Auth)

## AgentCore Identity のユースケース

1. Inbound Auth
    1. AgentCore Runtime で動作する Agent の呼び出しに Bearer トークンが必要という構成にする
    2. AgentCore Gateway と統合したツールの呼び出し時に Bearer トークンが必要という構成にする

2. Outbound Auth
    - AgentCore Identity を使用し Agent が外部サービスを呼び出すときと API キーを取得する

---
## Outbound Auth


### AgentCore Identity を使用し Agent が外部サービスを呼び出すときと API キーを取得する

![in1](images/identity_out1.png)

#### サンプル 1
* **main-apiKey-OpenWeather.py**
* このサンプルコードでは Agent ではなく通常の Python コードから OpenWeather の API キーを取得し、シアトルの天候情報を取得する

##### 準備

1. OpenWeather の API キーを入手しておく (無料)
    - https://openweathermap.org/

1. AWS マネジメントコンソールで AgentCore Identity の API キーを作成

1. Anthropic の SDK のインストール

    ```
    pip3 install requests asyncio
    ```

##### 実行

1. サンプル実行

    ```
    python3 main-apiKey-OpenWeatgher.py
    ```

#### サンプル 2 
* **main-apiKey.py**
* このサンプルコードでは Agent ではなく通常の Python コードから API キーを取得し、Anthropic SDK を使用して Claude を呼び出す

##### 準備

1. Anthropic の API キーを入手しておく (有料)

1. AWS マネジメントコンソールで AgentCore Identity の API キーを作成

1. Anthropic の SDK のインストール

    ```
    pip3 install anthropic asyncio
    ```

##### 実行

1. サンプル実行

    ```
    python3 main-apiKey.py
    ```

---

#### その他のサンプル

* **create-api-key.py**
    - コードから AgentCore Identity で管理するキーを作成するサンプル
* **test-anthropic.py**
    - スタンドアローンで Anthropic の API キーを使用するサンプル
---
* 参考にしたブログ記事
  - https://qiita.com/moritalous/items/6c822e68404e93d326a4


