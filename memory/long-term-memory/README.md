# AgentCore Memory の Long-term memory を Strands Agent から使用する

* Strands Agents　ではデフォルトで SlidingWindowConversationManager で直近の会話履歴のみ保持している
    - 他の ConversationManager の使用も可能
* **このサンプルでは、AgentCore Memory の Long-term memory を会話のサマリーの取得に使用する**