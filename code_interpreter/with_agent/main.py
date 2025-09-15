import asyncio
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.tools.code_interpreter_client import code_session
from strands import Agent, tool

# システムプロンプトの定義
SYSTEM_PROMPT = """コードを実行して回答を検証してください。
利用可能なツール：
- execute_python: Pythonコードを実行"""

# コードインタープリターツールの定義
@tool
def execute_python(code: str, description: str = "") -> str:
    """Execute Python code in the sandbox."""
    if description:
        code = f"# {description}\n{code}"
    print(f"\n実行コード: {code}")
    # コードインタープリターセッション内でコードを実行
    try:
        with code_session("us-east-1") as code_client:
            response = code_client.invoke(
                "executeCode",
                {"code": code, "language": "python", "clearContext": False},
            )
            for event in response["stream"]:
                result = event["result"]
                # エラーチェック
                if result.get("isError", False):
                    error_content = result.get("content", [])
                    if error_content:
                        return (
                            f"エラー: {error_content[0].get('text', 'Unknown error')}"
                        )
                # 正常な実行結果を返す
                content = result.get("content", [])
                if content and content[0].get("type") == "text":
                    return content[0].get("text", "実行完了（出力なし）")
                return "実行完了"
    except Exception as e:
        return f"実行エラー: {str(e)}"

# ツール付きエージェントの設定
agent = Agent(tools=[execute_python], system_prompt=SYSTEM_PROMPT)

# BedrockAgentCoreアプリケーションの設定
app = BedrockAgentCoreApp()

#@app.entrypoint
def invoke(payload):
    """Process user input and return a response with code execution capability"""
    user_message = payload.get("prompt", "Hello")
    async def run_agent():
        response_text = ""
        async for event in agent.stream_async(user_message):
            if "data" in event:
                chunk = event["data"]
                response_text += chunk
        return response_text
    # asyncio.run で非同期処理を実行
    try:
        response = asyncio.run(run_agent())
        return response
    except Exception as e:
        print(f"エージェント実行エラー: {str(e)}")
        return f"処理中にエラーが発生しました: {str(e)}"

if __name__ == "__main__":
    prompt = "次に挙げる複数の値の平均値を、コードを実行して求めて下さい。 1231, 3423, 2342, 7732, 2342"
    payload = {"prompt": prompt}
    response = invoke(payload)
    print(response)
#     app.run()