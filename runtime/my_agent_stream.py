from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
agent = Agent()

@app.entrypoint
async def agent_invocation(payload):
    """Handler for agent invocation"""
    user_message = payload.get(
        "prompt", "入力にプロンプ​​トが見つかりません。プロンプトキーを使用して JSON ペイロードを作成するようにクライアントに指示してください。"
    )
    stream = agent.stream_async(user_message)
    async for event in stream:
        #print(event)
        yield (event) # eventは辞書型出ないので特定部分だけを取り出すには工夫が必要

if __name__ == "__main__":
    app.run()