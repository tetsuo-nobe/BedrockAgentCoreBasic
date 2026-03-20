# Amazon Bedrock AgentCore Policy クイックスタート

Amazon Bedrock AgentCore の Policy 機能を使って、MCP Gateway 経由のツール呼び出しにガバナンス（アクセス制御）を適用するサンプルです。

返金処理ツール (`process_refund`) に対して Cedar ポリシーで金額上限を設定し、上限以下のリクエストは許可・上限以上は拒否される動作を確認できます。

## 構成

```
agentcore-policy-quickstart/
├── setup_policy.py   # リソースの一括セットアップ
├── test_policy.py    # ポリシー動作のテスト
├── clear_policy.py   # リソースの一括削除
├── config.json       # セットアップ後に生成される設定ファイル
└── README.md
```

## 前提条件

- Python 3.10 以上
- AWS 認証情報が設定済み（`aws configure` 等）
- `bedrock-agentcore-starter-toolkit` がインストール済み
- `requests` ライブラリがインストール済み

```bash
pip install bedrock-agentcore-starter-toolkit requests
```

## セットアップで作成されるリソース

`setup_policy.py` を実行すると、以下のリソースが自動的に作成されます。

1. **Cognito OAuth 認証サーバー** — Gateway へのアクセス認証用
2. **MCP Gateway** — ツール呼び出しのエンドポイント
3. **Lambda 関数 (RefundTool)** — 返金処理を行うツール本体
4. **Gateway ターゲット (RefundTarget)** — Lambda を Gateway に接続
5. **Policy Engine (RefundPolicyEngine)** — ポリシー評価エンジン
6. **Cedar ポリシー (refund_limit_policy)** — 返金金額の上限ルール（デフォルト: $1,000 未満を許可）

Policy Engine は **ENFORCE モード** で Gateway にアタッチされます。

## 使い方

### 1. セットアップ

```bash
python setup_policy.py
```

全リソースが作成され、接続情報が `config.json` に保存されます。完了まで数分かかります。

### 2. テスト

```bash
python test_policy.py
```

以下の 2 つのリクエストが実行されます。

| テスト | 金額 | 期待結果 |
|--------|------|----------|
| Test 1 | $500 | 許可（上限以下） |
| Test 2 | $2,000 | 拒否（上限超過） |

### 3. クリーンアップ

```bash
python clear_policy.py
```

作成した Policy、Policy Engine、Gateway を削除します。

## Cedar ポリシーの内容

```cedar
permit(principal,
  action == AgentCore::Action::"RefundTarget___process_refund",
  resource == AgentCore::Gateway::"<gateway_arn>")
when { context.input.amount < 1000 };
```

`context.input.amount` が 1,000 未満の場合のみツール呼び出しを許可します。

## 参考

- [Amazon Bedrock AgentCore ドキュメント](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
