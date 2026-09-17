# AgentCore Memory サンプル (AWS SDK / boto3 版)

AWS SDK for Python (boto3) を直接使って、AgentCore Memory の短期記憶(イベント)の
書き込み・取得を確認する最小サンプルです。

- 使用するメモリリソースは**事前に作成済み**であることを前提とします(このサンプルではメモリの作成は行いません)。
- `bedrock-agentcore` (データプレーン) クライアントの `create_event` / `list_events` のみを使用します。

## 前提条件

- Python 3.13 以上
- [uv](https://docs.astral.sh/uv/) がインストールされていること
- AWS認証情報が設定済みであること (`aws configure` など)
- AgentCore Memory リソースが作成済みであること

## セットアップ

```powershell
uv sync
```

## 環境変数の設定

```powershell
$env:MEMORY_ID = "mem-xxxxxxxxxx"   # 作成済みのメモリID
$env:AWS_REGION = "ap-northeast-1"  # 省略時は ap-northeast-1 が使われます
```

## 実行方法

```powershell
uv run python short_term_memory_sample.py
```

## 実行内容

1. `create_event` で4件の会話ターン(ユーザー/アシスタント)を短期記憶に書き込みます。
2. `list_events` で書き込んだ会話履歴を取得し、順番に表示します。

正常に動作すると、書き込んだ4件の会話がそのまま取得できることを確認できます。
