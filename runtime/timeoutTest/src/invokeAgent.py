import boto3
import json
from botocore.config import Config

# 設定の定義
my_config = Config(
    connect_timeout=5,  # 接続タイムアウト (秒)
    read_timeout=1200,   # 読み込みタイムアウト (秒) 
    retries={
        'mode': 'standard', # リトライモード ('legacy', 'standard', 'adaptive')
        'total_max_attempts': 1 # 最大試行回数
    }
)

#prompt = "こんにちは！"
prompt = "timeout"

client = boto3.client('bedrock-agentcore', region_name='us-east-1', config=my_config)
payload = json.dumps({"prompt": prompt})

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:068048081706:runtime/timeoutTest_Agent-xSlEd4GQ5b',
    runtimeSessionId='C-1234567890-1234567890-1234567890', # Must be 33+ char. Every new SessionId will create a new MicroVM
    payload=payload
)
response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)