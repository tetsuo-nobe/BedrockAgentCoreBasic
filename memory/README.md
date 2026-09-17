# AgentCore Memory サンプル集

Amazon Bedrock AgentCore Memory の「短期記憶(Short-Term Memory)」および
「長期記憶(Long-Term Memory)」の動作を、API の抽象度が異なる4つのパターンで
確認するための学習用サンプルです。

いずれのサンプルも、AgentCore Memory リソースは**事前に作成済み**であることを前提とし、
メモリID は環境変数から取得します(サンプル内でのメモリ作成は行いません)。

## サンプル一覧

| フォルダ | パターン | 使用する主なAPI/パッケージ |
|---|---|---|
| `aws_sdk/` | AWS SDK (boto3) を直接使用 | `boto3` (`bedrock-agentcore-control` / `bedrock-agentcore`) |
| `agentcore_sdk/` | AgentCore Python SDK を使用 | `bedrock_agentcore` パッケージの `MemoryClient` |
| `strands_sdk/` | Strands Agents SDK のセッションマネージャー(完成品)と統合 | `strands-agents` + `bedrock_agentcore` の Strands 統合モジュール (`AgentCoreMemorySessionManager`) |
| `strands_hooks/` | Strands Agents SDK の汎用フック機構を使い、自分でAgentCore SDK呼び出しを組み込む | `strands-agents` の `HookProvider`/`HookRegistry` + `bedrock_agentcore` の `MemoryClient` |

それぞれの抽象度の違いは以下の通りです。

- **AWS SDK**: 最も低レベル。イベントの payload 構造などを自分で組み立てる必要があるが、細かい制御が可能。
- **AgentCore SDK**: `MemoryClient` が boto3 呼び出しをラップし、簡潔なメソッド(`create_event`, `list_events` など)を提供。
- **Strands SDK 統合**: `AgentCoreMemorySessionManager` を Strands の `Agent` に渡すことで、会話の記録・呼び出しが自動化される。AWS製の完成品を使うパターン。
- **Strands hooks**: Strandsの汎用フック機構(`HookProvider`)の上に、`MemoryClient`呼び出しを自分で実装するパターン。`strands_sdk/`と使うパッケージ自体は同じだが、保存・読み込みのタイミングやロジックを自由に制御できる。AWS公式ワークショップのノートブックもこのパターンを採用している。

## 長期記憶(User Preference戦略)のサンプル

`strands_sdk/` と `strands_hooks/` には、短期記憶に加えて長期記憶(User Preference戦略)の
サンプル (`long_term_memory_preference_sample.py`) もあります。使用するメモリリソースに
User Preference戦略が設定されている必要があります。詳細は各フォルダの README を参照してください。

## 共通の前提

- Python 3.13 以上
- AWS認証情報が設定済み(`aws configure` など)
- AgentCore Memory リソースが作成済みで、そのメモリID を把握していること

各サンプルフォルダの README に、詳細な実行手順を記載しています。

## AWS マネジメントコンソールを使用した AgentCore Memory の作成手順
- 検索で `agentcore` と入力して **Amazon Bedrock AgentCore** のページを開きます。
- 左側のナビゲーションメニューから **構築** - **メモリー** を選択します。
- **メモリを作成** をクリックします。
- **メモリ 名前** に任意の名前を入力します。
- **短期メモリ (生のイベント) の有効期限** に必要な日数を指定します。
- **長期メモリ抽出戦略 - オプション** で **組み込み戦略** で **戦略の追加 (Add strategy)** - **ユーザープリファレンス** をクリックします。
- **戦略の名前** に任意の名前を入力します。
- **戦略の作成 (Create strategy)** をクリックします。
- **メモリを作成** をクリックします。
- **メモリの詳細** セクションを展開して **ステータス** が **作成中** から **アクティブ** に変わればメモリの作成完了です。
