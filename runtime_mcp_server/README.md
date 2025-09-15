# MCP Server を AgentCore runtime でデプロイする

* https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html

```
pip install mcp
```


```
python my_mcp_server.py
```

```
pip install bedrock-agentcore-starter-toolkit
```

```
agentcore configure -e my_mcp_server.py --protocol MCP
```

```
agentcore launch
```

```
export AGENT_ARN="agent_arn"

export BEARER_TOKEN="bearer_token"
```