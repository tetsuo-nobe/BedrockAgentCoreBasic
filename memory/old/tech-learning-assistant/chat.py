#!/usr/bin/env python3
"""
Tech Learning Assistant - 簡単チャットクライアント

使い方:
    python chat.py "質問内容"
    python chat.py "質問内容" --user "ユーザー名"
    python chat.py "質問内容" --session "セッションID"
"""

import boto3
import json
import uuid
import sys
import argparse
import os
from dotenv import load_dotenv

load_dotenv()

class TechLearningAssistantClient:
    def __init__(self):
        self.client = boto3.client('bedrock-agentcore', region_name='us-west-2')
        # 環境変数からAgent Runtime ARNを取得
        self.agent_arn = os.getenv("AGENT_RUNTIME_ARN")
        if not self.agent_arn:
            raise ValueError("AGENT_RUNTIME_ARN環境変数が設定されていません")
        self.default_session_id = None
        self.default_actor_id = "default_user"

    def chat(self, message, actor_id=None, session_id=None):
        """エージェントにメッセージを送信して応答を取得"""

        if not actor_id:
            actor_id = self.default_actor_id
        if not session_id:
            if not self.default_session_id:
                self.default_session_id = str(uuid.uuid4())
            session_id = self.default_session_id

        runtime_session_id = str(uuid.uuid4())

        payload = json.dumps({
            "prompt": message,
            "actor_id": actor_id,
            "session_id": session_id
        }).encode()

        try:
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_arn,
                runtimeSessionId=runtime_session_id,
                payload=payload
            )

            content_parts = []
            for chunk in response["response"]:
                try:
                    decoded = chunk.decode('utf-8')
                    content_parts.append(decoded)
                except UnicodeDecodeError:
                    decoded = chunk.decode('utf-8', errors='ignore')
                    content_parts.append(decoded)

            full_response = ''.join(content_parts)

            # JSONレスポンスの場合は整形
            try:
                json_response = json.loads(full_response)
                return json.dumps(json_response, ensure_ascii=False, indent=2)
            except:
                return full_response.strip('"')

        except Exception as e:
            return f"❌ エラーが発生しました: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Tech Learning Assistant チャットクライアント')
    parser.add_argument('message', nargs='?', help='質問メッセージ')
    parser.add_argument('--user', '-u', help='ユーザーID（actor_id）')
    parser.add_argument('--session', '-s', help='セッションID')

    args = parser.parse_args()

    client = TechLearningAssistantClient()

    if args.user:
        client.default_actor_id = args.user

    if args.session:
        client.default_session_id = args.session

    if args.message:
        response = client.chat(args.message)
        print(response)
    else:
        # デフォルトテスト
        print("🎓 Tech Learning Assistant テストモード")
        print("=" * 50)

        test_questions = [
            "Pythonの非同期プログラミングについて教えて",
            "私の学習進捗を分析してください",
            "苦手分野を教えて"
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. {question}")
            response = client.chat(question)
            print(f"回答: {response[:200]}...")

if __name__ == "__main__":
    main()
