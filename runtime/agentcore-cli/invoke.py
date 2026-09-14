import boto3
import json
import uuid

# セッションIDをUUIDで生成
session_id = str(uuid.uuid4())

# AgentCore のクライアントオブジェクトを作成
client = boto3.client('bedrock-agentcore')

# AgentCore ランタイムを呼び出す
response = client.invoke_agent_runtime(
    agentRuntimeArn="YOUR_AGENT_RUNTIME_ARN", # ランタイム ARN を記載
    runtimeSessionId=session_id,
    payload=json.dumps({"prompt": "こんにちは"})
)

# レスポンスからテキスト内容を取り出して表示
content = response["response"].read().decode('utf-8')
print(json.loads(content))