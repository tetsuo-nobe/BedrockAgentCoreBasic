# AgentCore Memory サンプル (Strands Agents SDK 統合版)

Strands Agents SDK の `AgentCoreMemorySessionManager` を `Agent` に渡すことで、
会話イベントの書き込みや長期記憶の検索を自動化するパターンのサンプルです。

| ファイル | 内容 |
|---|---|
| `short_term_memory_sample.py` | 短期記憶(イベント)の書き込み・取得を確認する |
| `long_term_memory_preference_sample.py` | 長期記憶(User Preference戦略)がセッションをまたいで反映されることを確認する |

- 使用するメモリリソースは**事前に作成済み**であることを前提とします(このサンプルではメモリの作成は行いません)。
- Agent との会話は `AgentCoreMemorySessionManager` によって自動的に短期記憶へ書き込まれます。

`aws_sdk/` / `agentcore_sdk/` と異なり、`create_event` を明示的に呼ぶコードは書きません。
Agentとの対話がそのまま短期記憶になる点がこのパターンの特徴です。

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

1. `AgentCoreMemoryConfig` で memory_id / actor_id / session_id を設定します。
2. `AgentCoreMemorySessionManager` を `with` ブロックで作成し、`Agent(session_manager=...)` に渡します。
3. `agent("発言内容")` を2回呼び出します。ユーザーの発言とアシスタントの応答は、裏側で自動的に短期記憶(イベント)へ書き込まれます。
4. `with` ブロックを抜けると、バッファに残っているメッセージがフラッシュされます。
5. 確認のため、AgentCore SDK の `MemorySessionManager.list_events` で書き込まれた会話履歴を取得して表示します。

正常に動作すると、Agentとの2往復(ユーザー発言+アシスタント応答)の会話が短期記憶から取得できることを確認できます。

## long_term_memory_preference_sample.py の実行内容

同じ actor_id (ユーザー) で、session_id (会話) だけを変えて2回のセッションを行い、
1回目に伝えた「好み」が2回目のセッションでも反映されるかを確認します。

1. 1回目のセッションで、Agent に好きなスポーツ(サッカー)・ファッションの好み(モノトーン)・
   好きな映画(ノーラン監督のSF映画)について伝えます。
2. User Preference戦略による長期記憶への抽出は非同期処理のため、少し待ちます(既定90秒。
   実測で1回目のセッション終了から抽出完了まで約90秒かかるケースが確認されているため、
   短すぎる待機時間だと抽出前に2回目のセッションが始まってしまいます)。
3. `MemoryClient.retrieve_memories` で、長期記憶に抽出された好みの情報を直接検索して表示します。
4. 別の session_id で2回目のセッションを開始します。このとき `AgentCoreMemoryConfig` の
   `retrieval_config` に、`MemoryClient.get_memory_strategies()` で取得した
   **このメモリに実際に設定されている名前空間テンプレート**(`namespaceTemplates`)を
   指定しているため、Agent への問いかけ時に関連する長期記憶が自動的にコンテキストへ注入されます。
   (詳細は次の「注意点」を参照)。
5. 2回目のセッションで「今週末に観る映画のおすすめ」を尋ね、1回目に伝えた好み
   (SF映画・ノーラン監督など)を踏まえた回答になっているかを確認します。

長期記憶への抽出タイミングはLLMによる非同期処理のため、実行環境によっては90秒待っても
まだ反映されていないことがあります。その場合は `WAIT_SECONDS_FOR_EXTRACTION` の値をさらに
増やして再実行してみてください。

## 注意点: 名前空間テンプレートを仮定で書いてはいけない

AWS公式ドキュメントには User Preference戦略の既定名前空間として
`/strategy/{memoryStrategyId}/actors/{actorId}/` (単数形)、SDKの内部実装(既定値)を見ると
`/strategies/{memoryStrategyId}/actors/{actorId}/` (複数形)という記載がありますが、
**実際にそのメモリに設定されている名前空間テンプレートは、メモリ作成時の設定内容次第で
これらとは異なる場合があります**。値を仮定してハードコードすると、検索結果が0件になり、
長期記憶がまったくコンテキストに注入されないという事象が起きます(エラーにはならないため
気づきにくい落とし穴です)。

これを避けるため、本サンプルでは `MemoryClient.get_memory_strategies(memory_id=...)` で、
このメモリに実際に設定されている `memoryStrategyId` と `namespaceTemplates` を取得し、
それをそのまま `retrieval_config` のキーとして使っています。

```python
strategy = get_user_preference_strategy(memory_client)  # 実際の設定を取得
namespace_template = strategy["namespaceTemplates"][0]   # 例: "/strategies/{memoryStrategyId}/actors/{actorId}/"
strategy_id = strategy["memoryStrategyId"]                # 例: "preference_builtin_xxxxx-yyyyyyyy"

retrieval_config = {
    namespace_template: RetrievalConfig(top_k=5, relevance_score=0.0, strategy_id=strategy_id),
}
```

なお `{memoryStrategyId}` プレースホルダー自体は、`RetrievalConfig(strategy_id=...)` を
明示的に指定しない限り空文字に置換されてしまう点にも注意してください
(SDK内部の `retrieve_customer_context` の実装より)。

## 注意点: 長期記憶が検索できても、Agentの回答に反映されないことがある

名前空間が正しく解決され、長期記憶の検索自体は成功していても(`[3]`で内容を確認可能)、
2回目のセッションでの回答が「あなたの好みをまだ知りません」のようになる場合、
主に次の2つが原因になります。

1. **system_prompt に「注入されたコンテキストを使う」指示がない**

   `AgentCoreMemorySessionManager` は、関連する長期記憶をユーザー発言の先頭に
   `<user_context>...</user_context>` タグとして自動的に埋め込みます(`context_tag`設定で
   タグ名は変更可能)。しかし、これを**実際に活用するかどうかはモデル側の判断**に委ねられます。
   `system_prompt` に「ユーザーについて知っていることを活用してください」といった指示が
   ないと、モデルが埋め込まれたコンテキストを無視してしまうことがあります。
   本サンプルの `SYSTEM_PROMPT` では、この点を明示的に指示しています。

2. **relevance_score の閾値で、関連する記憶が絞り込まれすぎている**

   `RetrievalConfig(relevance_score=...)` は、検索でヒットした記憶のうち
   このスコア以上のものだけをコンテキストに注入するフィルタです。
   ユーザーの質問文(例:「今週末に観る映画のおすすめは?」)と記憶の内容
   (例:「SF映画が好きで、ノーラン監督の作品が好き」)の意味的な近さによってスコアが
   決まるため、質問の言い回しによっては閾値を超えず、記憶が0件になることがあります。
   本サンプルでは学習用に `relevance_score=0.0` として、閾値による絞り込みを実質無効化しています。

実際に動作確認したところ、主な原因は上記2つのうち**待機時間不足(30秒)**でした。
90秒に延ばし、`system_prompt`での指示を追加した状態で正常に動作しています。

なお `strands_hooks/long_term_memory_preference_sample.py`(パターン4)では、自作フックの中で
コンテキストを `<user_context>` タグではなく `"Customer Context:\n..."` という平文ラベルで
ユーザー発言に直接埋め込む方式にしています。どちらの形式でも動作すること自体は確認できているため、
形式の違いは動作の妨げにはなりません。パターン3(このサンプル)は`AgentCoreMemorySessionManager`が
タグ形式で埋め込む仕組み上、system_prompt側でタグの扱いを明示的に指示する必要がある、という
使い方の違いがある点に注意してください。

## 他パターンとの違い

| 項目 | AWS SDK / AgentCore SDK | Strands SDK 統合 |
|---|---|---|
| イベントの書き込み | `create_event` / `add_turns` を明示的に呼ぶ | `agent()` を呼ぶだけで自動的に書き込まれる |
| 会話の管理 | 自分でメッセージを組み立てる | `Agent` が会話履歴・応答生成を管理する |
| 用途 | 細かい制御、フレームワーク非依存 | Strands Agents で実際にエージェントを動かしながら記憶を使う |

## 注意点: イベントのpayload構造

Strands統合は、会話テキストをそのまま `conversational.content.text` に格納するのではなく、
Strands の `SessionMessage`(ロール・コンテンツ・メタデータなどを含むオブジェクト)を
`json.dumps()` した文字列として格納します。

そのため `list_events` で取得した `text` は一見文字化けのような `\uXXXX` 表記のJSON文字列に見えますが、
これは日本語が正しく `ensure_ascii=True` でエスケープされているだけで、データの破損ではありません。
実際の発言内容を得るには、`text` をさらに `json.loads()` してから `message.content` を取り出す必要があります
(本サンプルの `[2]` の部分で実施しています)。

`aws_sdk/` や `agentcore_sdk/` のように直接 `create_event` / `add_turns` を呼ぶパターンでは、
`content.text` に発言テキストがそのまま入るため、この変換は不要です。

## 注意点: batch_size と後始末

`AgentCoreMemoryConfig` で `batch_size` を1より大きくした場合、メッセージは複数件まとめて送信するためにバッファされます。
その場合は本サンプルのように `with` ブロックを使うか、明示的に `session_manager.close()` を呼ばないと、
バッファに残ったメッセージが短期記憶に書き込まれずに失われるので注意してください。
