import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='us-east-1')
payload = json.dumps({"prompt": "こんにちは。2の32乗はいくらですか？"})

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:000000000000:runtime/strands_claude_getting_started-R0fXNM6DeP',
    runtimeSessionId='CLIENT-SESSION-VSCODE-000000000001', # Must be 33+ char. Every new SessionId will create a new MicroVM
    payload=payload
)
response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)