import boto3
import json

client = boto3.client('bedrock-agentcore', region_name="us-east-1")

# Prepare the payload
payload = json.dumps({"prompt": "こんにちは！"}).encode()

response = client.invoke_agent_runtime(
    contentType='application/json',
    accept='application/json',
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:068048081706:runtime/my_agent-WQYg5iA14o',
    payload=payload
)
response_body = response['response'].read()
response_data = json.loads(response_body)
result = response_data['result']['content'][0]['text']
print("Agent Response:", result)

