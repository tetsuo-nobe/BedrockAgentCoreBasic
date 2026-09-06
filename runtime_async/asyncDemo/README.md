# asyncDemo — 非同期 / 長時間実行エージェント (AgentCore Runtime)

Amazon Bedrock AgentCore Runtime 上で、**非同期に長時間実行する**エージェントを動かすサンプルプロジェクトです。

エントリーポイントは即座にレスポンスを返し、実際の処理はバックグラウンドで継続します。処理中はセッションを Active (HealthyBusy) 状態に保つことで、アイドルタイムアウトによる実行環境の終了を回避します。

参考記事: [Amazon Bedrock AgentCore Runtime で実現する 非同期 / 長期実行エージェント](https://zenn.dev/aws_japan/articles/agentcore-async-long-running-patterns)

## 仕組み

AgentCore Runtime の platform は約 2 秒間隔でエージェントの `/ping` エンドポイントを呼び出し、その応答でセッション状態を判定します。

| `/ping` の応答 | セッション状態 | アイドルタイムアウト |
| --- | --- | --- |
| `Healthy` | Idle | カウントが進む (= 環境を維持しない) |
| `HealthyBusy` | Active | 発火しない (= 環境を維持する) |

このサンプルでは Bedrock AgentCore Python SDK の `add_async_task()` / `complete_async_task()` を使い、以下の流れで HealthyBusy を制御します。

1. `add_async_task()` を呼ぶと内部カウンタが増え、`/ping` が自動で `HealthyBusy` を返すようになる
2. `asyncio.create_task()` でバックグラウンド処理を起動し、entrypoint は即座にレスポンスを返す (15 分の Request timeout に抵触しない)
3. バックグラウンド処理の完了時に `complete_async_task()` を呼ぶとカウンタが減り、0 になると `/ping` が `Healthy` に戻る

`complete_async_task()` は `try/finally` で必ず呼びます。呼び忘れると HealthyBusy が永続し、`maxLifetime` に達するまで実行環境が終了せず課金が続きます。

## プロジェクト構成

```
asyncDemo/
├── README.md                 # このファイル
├── AGENTS.md                 # AI コーディングアシスタント向けのプロジェクトコンテキスト
├── invoke.py                 # デプロイ済みエージェントを呼び出すクライアント
├── agentcore/
│   ├── agentcore.json        # プロジェクト設定 (ライフサイクル設定を含む)
│   ├── aws-targets.json      # デプロイ先 (アカウント + リージョン)
│   ├── .llm-context/         # スキーマの型定義
│   └── cdk/                  # CDK インフラ (@aws/agentcore-cdk)
└── app/
    └── AsyncAgent/
        ├── main.py           # エージェント本体 (非同期 / 長時間実行パターン)
        ├── pyproject.toml    # Python 依存関係
        └── uv.lock
```

## エージェントの動作 (main.py)

entrypoint はストリーミングを使わず、通常の async 関数として辞書を返します (SDK が JSON レスポンスとして返します)。`action` によって 2 つの操作を提供します。

### `action="start"` — 非同期ジョブを開始する

`add_async_task()` で HealthyBusy に遷移させ、バックグラウンド処理を起動して即座に応答を返します。

- `prompt` (任意): エージェントへのプロンプト
- `duration` (任意, 秒): 意図的な遅延秒数。長時間実行の検証用。`0` (デフォルト) は遅延なし。指定すると `asyncio.sleep` でその秒数だけ待機し、60 秒ごとに経過ログを出力してからエージェントを実行する

レスポンス例:

```json
{"status": "started", "task_id": 46993265423530186, "duration": 10}
```

### `action="status"` — 実行中ジョブを確認する

現在アクティブな非同期タスクの情報を返します。

レスポンス例 (実行中):

```json
{"active_count": 1, "running_jobs": [{"name": "long_job", "duration": 3.5}]}
```

`active_count` が 1 以上なら HealthyBusy を維持中 (= 実行環境が維持されている) と判断できます。処理完了後は `active_count` が 0 に戻ります。

## ライフサイクル設定 (agentcore.json)

`app/AsyncAgent` runtime の `lifecycleConfiguration` で、セッションのライフサイクルを制御しています。

```json
"lifecycleConfiguration": {
  "idleRuntimeSessionTimeout": 300,
  "maxLifetime": 600
}
```

| パラメータ | このプロジェクトの値 | デフォルト値 | 説明 |
| --- | --- | --- | --- |
| `idleRuntimeSessionTimeout` | 300 秒 (5 分) | 900 秒 (15 分) | セッションがアイドル (`/ping` が `Healthy`) のまま経過すると終了する。HealthyBusy を返し続ければ回避できる |
| `maxLifetime` | 600 秒 (10 分) | 28800 秒 (8 時間) | セッションの絶対的な寿命。状態に関わらず到達すると強制終了する。HealthyBusy でも回避できない |

> **Note**
> このプロジェクトは検証用に短い値を設定しています。HealthyBusy を返し続けても `maxLifetime` (10 分) を超えると強制終了します。10 分を超える長時間ジョブを完走させたい場合は `maxLifetime` を延ばしてください。
> - Runtime microVMs (このプロジェクトの `networkMode: PUBLIC` 構成): `maxLifetime` は最大 8 時間
> - Runtime Instances (capacity provider 構成): `maxLifetime` は最大 14 日

## 使い方

### 前提条件

- Node.js 20.x 以上
- Python 3.10 以上 + [uv](https://docs.astral.sh/uv/getting-started/installation/)
- AWS 認証情報が設定済み (`aws configure` または環境変数)
- boto3 に `bedrock-agentcore` クライアントが含まれるバージョン

### デプロイ

```powershell
agentcore deploy    # CDK を合成して AWS にデプロイ
agentcore status    # デプロイ状況と Runtime ARN を確認
```

`main.py` や `agentcore.json` を変更した場合は、`agentcore deploy` で再デプロイして反映します。

### 呼び出し (invoke.py)

`invoke.py` の冒頭の `REGION` と `AGENT_RUNTIME_ARN` を、`agentcore status` で取得した値に合わせて設定してください。

```powershell
# 10 秒の遅延ジョブを開始 (同一セッションを維持したいので session-id を固定)
python invoke.py start --duration 10 --session-id longrun-session-0001-0000000000000000

# 同じ session-id で進捗を確認 (active_count が 1 なら HealthyBusy 維持中)
python invoke.py status --session-id longrun-session-0001-0000000000000000
```

`invoke.py` のオプション:

| オプション | 説明 |
| --- | --- |
| `action` | `start` (ジョブ開始) または `status` (状態確認) |
| `--prompt` | エージェントへのプロンプト (`start` で使用) |
| `--duration` | 意図的な遅延秒数 (`start` で使用)。`0` は遅延なし |
| `--session-id` | `runtimeSessionId` (33 文字以上)。省略時は自動生成。状態確認では `start` 時と同じ値を指定すること |

> **Important**
> 非同期ジョブの状態確認 (`status`) では、`start` 時と**同じ `session-id`** を指定してください。別の `session-id` を使うと別の実行環境になり、`active_count` が 0 に見えます。

### 動作の目安

`invoke.py` は呼び出しの所要時間を出力します。非同期パターンが正しく機能していれば、`--duration` の秒数に関わらず短時間 (通常 1 秒前後、ウォーム時) でレスポンスが返ります。

```
[invoke] invoke_agent_runtime() returned in 1.09s
[invoke] response body read in 0.00s (total 1.09s)
[invoke] response:
{"status": "started", "task_id": 46993265423530186, "duration": 10}
```

この時間はエージェント処理 (バックグラウンドで実行) ではなく、AgentCore Runtime の呼び出しオーバーヘッド (API 往復・ルーティング・コールドスタート有無) によるものです。

## ログの確認

バックグラウンド処理の進捗や `/ping` の状態遷移は runtime ログで確認できます。

```powershell
agentcore logs
```

`[Background] task_id=... | elapsed=Ns / durations` の経過ログや、`Ping: status=HealthyBusy, active_tasks=1` の状態遷移が記録されます。
