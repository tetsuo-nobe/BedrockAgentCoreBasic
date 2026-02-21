from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
import time

app = BedrockAgentCoreApp()
agent = Agent()

@app.entrypoint
def invoke(payload):
    """Process user input and return a response"""
    user_message = payload.get("prompt", "こんにちは。")

    if user_message == "timeout":
        print("----- start sleep -----")
        time.sleep(902)
        print("----- end sleep -----")
        
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()