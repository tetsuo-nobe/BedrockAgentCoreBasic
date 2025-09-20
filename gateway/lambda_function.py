# AgentCore Gateway のコンソールに表示されているコード
import json

def get_weather(location):
    return f"The weather in {location} is Sunny!"

def lambda_handler(event, context):
    print(event)
    toolName = context.client_context.custom['bedrockAgentCoreToolName']
    delimiter = "___"
    if delimiter in toolName:
        toolName = toolName[toolName.index(delimiter) + len(delimiter):]
    print(toolName)
    if toolName == 'get_weather':
        return {'statusCode': 200, 'body': get_weather(event['location'])}
