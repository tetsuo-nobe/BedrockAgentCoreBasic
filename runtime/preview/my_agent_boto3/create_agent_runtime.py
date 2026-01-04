import boto3

# Create the client
client = boto3.client('bedrock-agentcore-control', region_name="us-east-1")

# Call the CreateAgentRuntime operation
response = client.create_agent_runtime(
    agentRuntimeName='hello_agent',
    agentRuntimeArtifact={
        'containerConfiguration': {
            'containerUri': '123456789012.dkr.ecr.us-east-1.amazonaws.com/my-agent:latest'
        }
    },
    networkConfiguration={"networkMode":"PUBLIC"},
    roleArn='arn:aws:iam::123456789012:role/AgentRuntimeRole'
)