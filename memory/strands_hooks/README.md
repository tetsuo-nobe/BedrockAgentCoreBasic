# AgentCore Memory サンプル (Strands hooks + AgentCore SDK 版)

Strands Agents SDK の汎用フック機構 (`HookProvider` / `HookRegistry`) を自分で実装し、
その中で AgentCore Python SDK (`MemoryClient`) を呼び出して、短期記憶・長期記憶の
書き込み・取得を自前で組み立てるパターンのサンプルです。

- 使用するメモリリソースは**事前に作成済み**であることを前提とします(このサンプルではメモリの作成は行いません)。
- `strands_sdk/`(パターン3)が AWS製の完成品 `AgentCoreMemorySessionManager` を使うのに対し、
  このサンプルは同じ処理を自分でフックとして実装します。

| ファイル | 内容 |
|---|---|
| `short_term_memory_sample.py` | 短期記憶(イベント)の書き込み・取得を確認する |
| `long_term_memory_preference_sample.py` | 長期記憶(User Preference戦略)がセッションをまたいで反映されることを確認する |

## 前提条件

- Python 3.13 以上
- [uv](https://docs.astral.sh/uv/) がインストールされていること
- AWS認証情報が設定済みであること (`aws configure` など)
- Amazon Bedrock でモデル(Claude など)が利用可能であること
- AgentCore Memory リソースが作成済みであること
- `long_term_memory_preference_sample.py` を実行する場合は、そのメモリに
  User Preference戦略 (`userPreferenceMemoryStrategy`) が設定されていること

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
# 短期記憶の確認
uv run python short_term_memory_sample.py

# 長期記憶(User Preference戦略)の確認
uv run python long_term_memory_preference_sample.py
```

## short_term_memory_sample.py の実行内容

1. `ShortTermMemoryHook` という自作の `HookProvider` を定義します。このフックは次の2つのイベントを購読します。
   - `AgentInitializedEvent`: Agent起動時に `MemoryClient.get_last_k_turns` で過去の会話履歴を読み込み、`system_prompt` に注入する
   - `MessageAddedEvent`: メッセージが追加されるたびに `MemoryClient.create_event` でAgentCore Memoryへ書き込む
2. `Agent(hooks=[...], state={...})` の `state` に `actor_id` / `session_id` を保持させ、フック内で参照します。
3. `agent("発言内容")` を2回呼び出します。ユーザーの発言とアシスタントの応答は、`MessageAddedEvent`フック経由で自動的に短期記憶(イベント)へ書き込まれます。
4. 確認のため、`MemoryClient.list_events` で書き込まれた会話履歴を取得して表示します。

正常に動作すると、Agentとの2往復(ユーザー発言+アシスタント応答)の会話が短期記憶から取得できることを確認できます。

## long_term_memory_preference_sample.py の実行内容

AWS公式ワークショップのノートブック(`CustomerSupportMemoryHooks`)と同じ設計で、
`LongTermMemoryHook` という自作の `HookProvider` を定義します。このフックは次の2つの
イベントを購読します。

- `retrieve_customer_context` (`MessageAddedEvent`): ユーザー発言が追加された直後に
  `MemoryClient.retrieve_memories` で関連する長期記憶を検索し、
  `"Customer Context:\n{context}\n\n{元の質問}"` という形でユーザー発言の先頭に注入する
- `save_support_interaction` (`AfterInvocationEvent`): 応答が完了した後に、
  直近のユーザー発言とアシスタント応答のペアを `MemoryClient.create_event` で保存する

同じ actor_id (ユーザー) で、session_id (会話) だけを変えて2回のセッションを行い、
1回目に伝えた「好み」が2回目のセッションでも反映されるかを確認します。

1. 1回目のセッションで、Agent に好きなスポーツ(サッカー)・ファッションの好み(モノトーン)・
   好きな映画(ノーラン監督のSF映画)について伝えます。各やり取りは`AfterInvocationEvent`フックで
   自動的にAgentCore Memoryへ保存されます。
2. User Preference戦略による長期記憶への抽出は非同期処理のため、少し待ちます(既定90秒)。
3. `MemoryClient.retrieve_memories` で、長期記憶に抽出された好みの情報を直接検索して表示します。
4. 別の session_id で2回目のセッションを開始します。`retrieve_customer_context`フックにより、
   Agentへの問いかけ時に関連する長期記憶が自動的にコンテキストへ注入されます。
5. 2回目のセッションで「今週末に観る映画のおすすめ」を尋ね、1回目に伝えた好み
   (SF映画・ノーラン監督など)を踏まえた回答になっているかを確認します。

長期記憶への抽出タイミングはLLMによる非同期処理のため、実行環境によっては90秒待っても
まだ反映されていないことがあります。その場合は `WAIT_SECONDS_FOR_EXTRACTION` の値を増やして
再実行してみてください。

### strands_sdk/long_term_memory_preference_sample.py との違い

`strands_sdk/`版は `AgentCoreMemorySessionManager` の `retrieval_config` に
名前空間テンプレートをそのまま設定として渡す方式でしたが、こちらは `MessageAddedEvent` フックの
中で `retrieve_memories(namespace=...)` を直接呼び出します。コンテキストの注入形式も
`<user_context>`タグではなく `"Customer Context:\n..."` という平文ラベルにしている点が異なります
(ノートブックの実装に合わせています)。

## パターン3 (strands_sdk/) との違い

| 項目 | strands_sdk/ (パターン3) | strands_hooks/ (パターン4) |
|---|---|---|
| 使うもの | `AgentCoreMemorySessionManager` (AWS製の完成品) | `strands.hooks` の `HookProvider` (汎用の下位レイヤー) + 自作コード |
| 書き込みのタイミング制御 | SDK側に一任 (バッファリング設定などはあるが基本お任せ) | `MessageAddedEvent` を自分でフックするので、保存するかどうか・保存内容を自由に制御できる |
| 読み込みのタイミング制御 | SDK側の`retrieval_config`に従う | `AgentInitializedEvent` を自分でフックするので、読み込み件数・注入方法を自由に制御できる |
| 実装の手間 | 少ない(設定を渡すだけ) | 多い(フックのロジックを自分で書く) |
| 用途 | 素早く組み込みたい | 独自の保存・検索ロジックを組み込みたい、複数フレームワーク共通の記憶モジュールを自作したい |

payloadの構造(`conversational.content.text`)については、パターン4は`MemoryClient.create_event`に発言テキストをそのまま渡すため、`strands_sdk/`のように`json.loads`で二重にデコードする必要はありません。

## 使用パッケージ

- `strands-agents`: `Agent`本体、フック機構(`HookProvider`, `HookRegistry`)、イベント型(`AgentInitializedEvent`, `MessageAddedEvent`)
- `bedrock-agentcore`: `MemoryClient`(記憶の書き込み・取得。`agentcore_sdk/`サンプルと同じAPI)

新しいパッケージは増えず、上記2つを組み合わせて使います。
