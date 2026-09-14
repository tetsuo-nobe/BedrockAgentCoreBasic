from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp

# AI エージェントと API サーバーを作成
agent = Agent(model="us.anthropic.claude-sonnet-4-6")
app = BedrockAgentCoreApp()

# API サーバーのエントリポイントを設定
@app.entrypoint
async def invoke(payload, context):
    # プロンプトを取り出して AI エージェントを呼び出し
    prompt = payload.get("prompt")
    return agent(prompt)

# API サーバーを起動
if __name__ == "__main__":
    app.run()
