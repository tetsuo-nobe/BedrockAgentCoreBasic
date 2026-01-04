import boto3
import json
import secrets

client = boto3.client('bedrock-agentcore', region_name='ap-northeast-1')
payload = json.dumps({"prompt": "生成 AI についてを分かりやすく説明して下さい。"})

session_id = secrets.token_hex(17)

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:ap-northeast-1:068048081706:runtime/hosted_agent_qfyms-i4HsycAHGS',
    runtimeSessionId=session_id,
    payload=payload
)
response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)