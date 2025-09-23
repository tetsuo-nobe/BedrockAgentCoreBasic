# AgentCore Identity で、アウトバウンド認証用に管理する API KEY を作成する（マネコンからも作成可能）
from bedrock_agentcore.services.identity import IdentityClient
identity_client = IdentityClient(region="us-east-1")

api_key_provider = identity_client.create_api_key_credential_provider({
    "name": "XXXX_API_KEY",
    "apiKey": "ABC1234" # Replace it with the API key you obtain from the external application vendor, e.g., OpenAI
})
print(api_key_provider)
