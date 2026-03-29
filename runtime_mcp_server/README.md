# MCP Server を AgentCore runtime でデプロイする

* S3 バケットからマークダウンファイルを取得して PowerPoint 形式のファイルに変換する MCP Server

```
pip3 install -r requirements.txt
```

```
agentcore configure -e convert_server.py --protocol MCP --disable-memory
```

* .bedrock_agentcore/ppt_convert_server/Dockerfile に Node.js と Marp をインストールするコマンドを追加
    - Dockerfile_add.txt の内容を ENV コマンドと COPY コマンドの間に追記

```
agentcore deploy
```

* デプロイ完了後、Runtime の該当バージョンのリンクからロール名を確認し、S3 バケットへのアクセス許可ポリシーを追加する