from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

app = BedrockAgentCoreApp()

# ツールの定義
@tool
def calculator(operation: str, a: float, b: float) -> str:
    """
    基本的な計算を実行する電卓ツール

    Args:
        operation: 実行する演算 (add, subtract, multiply, divide)
        a: 最初の数値
        b: 2番目の数値

    Returns:
        計算結果
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero",
    }

    if operation not in operations:
        return f"Error: Unknown operation '{operation}'. Use: add, subtract, multiply, divide"

    result = operations[operation](a, b)
    return f"{a} {operation} {b} = {result}"

@tool
def get_weather(city: str) -> str:
    """
    指定された都市の天気情報を取得する（デモ用のモックデータ）

    Args:
        city: 都市名

    Returns:
        天気情報
    """
    weather_data = {
        "tokyo": {"temp": 15, "condition": "Sunny", "humidity": 45},
        "osaka": {"temp": 17, "condition": "Cloudy", "humidity": 60},
        "new york": {"temp": 8, "condition": "Rainy", "humidity": 80},
        "london": {"temp": 10, "condition": "Cloudy", "humidity": 75},
    }

    city_lower = city.lower()
    if city_lower in weather_data:
        data = weather_data[city_lower]
        return f"Weather in {city}: {data['condition']}, Temperature: {data['temp']}C, Humidity: {data['humidity']}%"
    else:
        return f"Weather information for {city} is not available"

@tool
def search_knowledge(query: str) -> str:
    """
    ナレッジベースを検索する（デモ用のモックデータ）

    Args:
        query: 検索クエリ

    Returns:
        検索結果
    """
    knowledge_base = {
        "python": "Python is a versatile high-level programming language known for readability and simplicity.",
        "aws": "Amazon Web Services (AWS) is a cloud computing platform.",
        "ai": "Artificial Intelligence (AI) enables machines to perform human-like intelligent tasks.",
        "bedrock": "Amazon Bedrock is a fully managed service for building generative AI applications.",
    }

    query_lower = query.lower()
    results = []
    for key, value in knowledge_base.items():
        if key in query_lower or query_lower in key:
            results.append(value)

    if results:
        return "\n".join(results)
    else:
        return f"No information found for '{query}'"

# エージェントの作成
agent = Agent(
    system_prompt="""You are a helpful AI assistant.
Use the available tools to provide accurate and useful responses.

Available tools:
- calculator: Perform mathematical calculations
- get_weather: Get weather information for a city
- search_knowledge: Search the knowledge base for information

Respond clearly and concisely.""",
    tools=[calculator, get_weather, search_knowledge],
)

@app.entrypoint
def invoke(payload):
    """AgentCore Runtime entrypoint"""
    user_message = payload.get("prompt", "Hello! How can I help you?")
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
