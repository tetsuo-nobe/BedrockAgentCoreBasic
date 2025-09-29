# AgentCore Browser に Browser-use で接続して、Yahoo の検索を使用する

* 下記のブログ記事のコードをベースにしています。
  - https://dev.classmethod.jp/articles/amazon-bedrock-agentcore-agentcore-browser-sample/

* Python 3.11 以上が必要

* Claude でクロスリージョン可能な基盤モデルを使用する
    - Claude 以外のモデルでは brouser-use を正常に扱えなかった
    - クロスリージョン以外のモデルではサポートされておらず実行に失敗する

```
pip install -r requirements.txt
```

```
python main.py
```


