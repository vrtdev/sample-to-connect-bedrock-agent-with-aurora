#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.rds_aurora_stack import RDSAuroraStack
from stacks.bedrock_agent_stack import BedrockAgentStack


app = cdk.App()

rds_aurora_stack = RDSAuroraStack(app, "RDSAuroraStack")

bedrock_agent_stack = BedrockAgentStack(app, "BedrockAgentStack")

app.synth()
