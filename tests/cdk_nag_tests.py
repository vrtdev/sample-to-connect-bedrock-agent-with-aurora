import pytest
import sys
import os
from aws_cdk import App, Aspects, Stack
from aws_cdk.assertions import Annotations, Match
from cdk_nag import AwsSolutionsChecks, NagSuppressions

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import all stacks
from stacks.rds_aurora_stack import RDSAuroraStack
from stacks.bedrock_agent_stack import BedrockAgentStack


def create_test_stack(stack_class, stack_name):
    # Update the app to include context
    app = App()

    stack = stack_class(app, stack_name)
    Aspects.of(stack).add(AwsSolutionsChecks())

    if stack_name == "RDSAuroraStack":
        NagSuppressions.add_stack_suppressions(
            stack,
            [
                {
                    "id": "AwsSolutions-SMG4",
                    "reason": "The secret does not have automatic rotation scheduled.",
                },
                {
                    "id": "AwsSolutions-RDS6",
                    "reason": "The RDS Aurora MySQL/PostgresSQL cluster does not have IAM Database Authentication enabled.",
                },
                {
                    "id": "AwsSolutions-RDS11",
                    "reason": "The RDS instance or Aurora DB cluster uses the default endpoint port.",
                },
            ],
        )

    if stack_name == "BedrockAgentStack":
        NagSuppressions.add_stack_suppressions(
            stack,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "The IAM user, role, or group uses AWS managed policies.",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "The IAM entity contains wildcard permissions and does not have a cdk-nag rule suppression with evidence for those permission.",
                },
            ],
        )

    return stack


@pytest.fixture(
    params=[
        (RDSAuroraStack, "RDSAuroraStack"),
        (
            BedrockAgentStack,
            "BedrockAgentStack",
        ),
        # Add more stacks here
    ]
)
def test_stack(request):
    stack_class, stack_name = request.param
    return create_test_stack(stack_class, stack_name)


def test_no_unsuppressed_warnings(test_stack):
    warnings = Annotations.from_stack(test_stack).find_warning(
        "*", Match.string_like_regexp("AwsSolutions-.*")
    )
    assert len(warnings) == 0, f"Unsuppressed warnings found in {test_stack.stack_name}"


def test_no_unsuppressed_errors(test_stack):
    errors = Annotations.from_stack(test_stack).find_error(
        "*", Match.string_like_regexp("AwsSolutions-.*")
    )
    assert len(errors) == 0, f"Unsuppressed errors found in {test_stack.stack_name}"
