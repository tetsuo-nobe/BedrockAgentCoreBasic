import boto3
import json
import uuid

client = boto3.client('bedrock-agentcore', region_name='us-west-2')
payload = json.dumps({"prompt": "こんにちは！"})

session_id = str(uuid.uuid4())

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-west-2:068048081706:runtime/myagent-RcLFq55IZq',
    runtimeSessionId=session_id, # Must be 33+ char. Every new SessionId will create a new MicroVM
    payload=payload
)
response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)