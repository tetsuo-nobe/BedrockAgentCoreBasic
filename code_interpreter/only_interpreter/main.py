import json
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter

# Configure and Start the code interpreter session
code_client = CodeInterpreter("us-east-1")
code_client.start()

# Execute the hello world code
response = code_client.invoke(
    "executeCode", {"language": "python", "code": 'print("Hello World!!!")'}
)

# Process and print the response
for event in response["stream"]:
    print(json.dumps(event["result"], indent=2))

# Clean up and stop the code interpreter sandbox session
code_client.stop()