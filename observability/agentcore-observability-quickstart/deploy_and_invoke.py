from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import time

boto_session = Session()
region = boto_session.region_name

agentcore_runtime = Runtime()
agent_name = "strands_claude_getting_started"

# 構成
response = agentcore_runtime.configure(
    entrypoint="strands_claude.py", 
    auto_create_execution_role=True,
    auto_create_ecr=True,
    requirements_file="requirements.txt", # make sure aws-opentelemetry-distro exists along with your libraries required to run your agent
    region=region,
    agent_name=agent_name
)

# ラウンチ
launch_result = agentcore_runtime.launch()
print(launch_result)

# 呼び出し
invoke_response = agentcore_runtime.invoke({"prompt": "How is the weather now?"})
print(invoke_response)