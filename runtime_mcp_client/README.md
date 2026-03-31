# AgentCore runtime にデプロイされた MCP Server を使用する

* runtime_mcp_server で作成した PPT コンバーターの MCP Server へアクセスする
    - 変換元のデータは DynamoDB テーブル tech-report に格納されている前提
        - Key : id
        - date : 日付
        - report : マークダウンの技術記事


* AWS のアクセスキー ID を環境変数で指定する

```
pip3 install -r requirements.txt
```

```
python3 agent.py
```
