# AgentCore harness サンプル (AWS SDK / boto3 版)

AWS SDK for Python (boto3) を直接使って、AgentCore harness を `InvokeHarness` で呼び出す最小サンプルです。

- `bedrock-agentcore` (データプレーン) クライアントの `invoke_harness` のみを使用します。
- `InvokeHarness` は IAM (SigV4) 認証で呼び出せるため、Bearer トークンの取得などは不要です。

## 前提条件

- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/) がインストールされていること
- AWS認証情報が設定済みであること (`aws configure` など)
- 呼び出す IAM プリンシパルに `bedrock-agentcore:InvokeHarness` の権限があること


## AgentCore harness の作成

このサンプルは呼び出し専用のため、harness を最初に作成しておく必要があります。

### AWS マネジメントコンソールを使用した AgentCore harness の作成手順
- 検索で `agentcore` と入力して **Amazon Bedrock AgentCore** のページを開きます。
- 左側のナビゲーションメニューから **ハーネスプレイグラウンド** を選択します。
- **新しいハーネスを作成** をクリックします。
- **ハーネス名** に `harness_99` と入力します。(**99 の部分はご自分の番号に置き換えます。**)
- **作成** をクリックします。
- **ハーネスプレイグラウンド** が表示されます。ページ下部で任意のプロンプトを入力して、正常に動作することを確認します。
- 左側のナビゲーションメニューから **エージェント** を選択します。
- 作成した AgentCore harness の名前のリンクをクリックします。
- **設定** タブをクリックし、**ハーネスの詳細** セクションを展開表示します。
- **ハーネス ARN** の値をコピーしてメモしておきます。

---
* 以降は参考です。

### AWS CLI の場合、最小構成であれば次のように作成できます。

```powershell
aws bedrock-agentcore-control create-harness `
  --harness-name "MyHarness" `
  --execution-role-arn "arn:aws:iam::123456789012:role/MyHarnessRole"
```

作成状況は `get-harness` で確認できます。`status` が `READY` になったら呼び出し可能です。

```powershell
aws bedrock-agentcore-control get-harness --harness-id "MyHarness-XyZ123"
```

レスポンスに含まれる `arn` の値を、上記「環境変数の設定」の `HARNESS_ARN` に設定してください。

参考: [AgentCore harness の使用開始](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-get-started.html)

---

## セットアップ

* Code Server のターミナルから下記を実行します。

```bash
cd  ~/environment/BedrockAgentCoreBasic/harness
```

```bash
uv sync
```

## 環境変数の設定

* 作成した AgentCore harness の ARN を環境変数に設定します。

```bash
export HARNESS_ARN="arn:aws:bedrock-agentcore:us-west-2:123456789012:harness/MyHarness-XyZ123"  # 作成済み harness の ARN
export AWS_REGION="us-west-2"  # 省略時は us-west-2 が使われます
export QUALIFIER="DEFAULT"     # 省略時は DEFAULT エンドポイントが使われます

```

* 下記は Windows の場合

```powershell
$env:HARNESS_ARN = "arn:aws:bedrock-agentcore:us-west-2:123456789012:harness/MyHarness-XyZ123"  # 作成済み harness の ARN
$env:AWS_REGION = "us-west-2"  # 省略時は us-west-2 が使われます
$env:QUALIFIER = "DEFAULT"     # 省略時は DEFAULT エンドポイントが使われます
```


## 実行

```bash
uv run invoke.py "5日間の東京旅行の予算内プランを考えてください。"
```

同じ会話を継続したい場合は、1回目に使われた `SessionId`(実行時に標準出力へ表示されます)を
環境変数 `SESSION_ID` に設定してから再度実行してください。

```bash
export SESSION_ID="(1回目の実行で表示された SessionId の値)"
uv run python invoke.py "さっきの続きで、予算をもう少し抑えたプランにしてください。"
```

## invoke.py の内容

1. `boto3.client("bedrock-agentcore")` を作成します。
2. `invoke_harness` に harness の ARN・セッションID・ユーザーメッセージを渡して呼び出します。
3. レスポンスはイベントストリームで返るため、テキストの差分(`contentBlockDelta`)を
   逐次表示しながら連結し、最終的な応答を表示します。

正常に動作すると、harness からの応答がストリーミングでそのまま標準出力に表示されます。

---


