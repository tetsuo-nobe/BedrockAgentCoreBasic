
* 参考ドキュメント: [Get started with AgentCore Observability](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-get-started.html)

* CloudWatch のトランザクション検索を有効化しておく
    - 有効化後、ロググループ **aws/spans** が作成されていることを確認する。
    - このロググループは絶対に削除してはいけない
    - 万が一間違って削除した場合は、CloudWatch の 「設定」メニューから X-Ray の トランザクション検索設定をいったん無効化して再度有効化することで再作成可能

* プロジェクトフォルダ作成
```
mkdir agentcore-runtime-quickstart
cd agentcore-runtime-quickstart
python3 -m venv .venv
source .venv/bin/activate
```

* パッケージインストール
```
pip install pip install 'strands-agents[otel]'
pip install bedrock_agentcore_starter_toolkit
```

* 先に AgentCore Memory を作成しておく
    - 作成後、strands_claude.py の中で memory id を指定する

* deploy_and_invoke.py を実行して Runtime にデプロイし、呼び出す
    - 動作しない場合は、マネコンからエンドポイントのセクションのログリンクからログを参照する
    - **注意** Memory へのアクセス権限がなく初回呼出しは失敗するはず
    - よって、作成されたロールに権限を付与して invoke_to_runtime.py を実行する

* さらに何度か呼び出す場合は、invoke_to_runtime.py を実行する

* その後、CloudWatch の AgentCore ダッシュボードを確認する
    - メトリクス、ログ、トレースが取得できているはず
