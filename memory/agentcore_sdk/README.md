# AgentCore Memory サンプル (AgentCore Python SDK 版)

AgentCore Python SDK (`bedrock-agentcore` パッケージ) の `MemorySessionManager` を使って、
AgentCore Memory の短期記憶(イベント)の書き込み・取得を確認する最小サンプルです。

- 使用するメモリリソースは**事前に作成済み**であることを前提とします(このサンプルではメモリの作成は行いません)。
- `MemorySessionManager` から作成した `MemorySession` の `add_turns` / `list_events` のみを使用します。

`aws_sdk/` の boto3 版と同じ処理を、より簡潔な API で行います。

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

1. `MemorySessionManager.create_memory_session` で actor/session に紐づいたセッションを作成します。
2. `session.add_turns` で4件の会話ターン(ユーザー/アシスタント)を短期記憶に書き込みます。
3. `session.list_events` で書き込んだ会話履歴を取得し、順番に表示します。

正常に動作すると、書き込んだ4件の会話がそのまま取得できることを確認できます。

## boto3版との違い

| 項目 | AWS SDK (boto3) | AgentCore SDK |
|---|---|---|
| クライアント | `bedrock-agentcore` クライアントを直接使用 | `MemorySessionManager` がラップ |
| メッセージの書き込み | `payload` の辞書構造を自分で組み立てる | `ConversationalMessage` オブジェクトを渡すだけ |
| actor_id/session_id | 呼び出しごとに毎回指定 | `create_memory_session` で一度だけ指定 |
