from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct

from search_content.constructs.lambda_create_indices import LambdaTriggers



class RoleAdminInit(Construct):

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.region = Stack.of(self).region
        self.account = Stack.of(self).account

        self.role_admin_init = self.buildRole()

    def buildRole(self)->_iam.Role:
        lambda_role = _iam.Role(
            self, 'Role',
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com')   # type: ignore
        )

        lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            'service-role/AWSLambdaBasicExecutionRole'
        ))

        lambda_role.attach_inline_policy(
            _iam.Policy(
                self, 'InlinePolicy',
                statements=[
                    _iam.PolicyStatement(
                        actions=["logs:CreateLogGroup"],
                        resources=[
                            f'arn:aws:logs:{self.region}:{self.account}:*'
                        ]
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'logs:CreateLogStream',
                            'logs:PutLogEvents'
                        ],
                        resources=[
                            f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/{LambdaTriggers.searchCfg.name}:*',
                            f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/{LambdaTriggers.vectorCfg.name}:*'
                        ]
                    ),
                ]
            )
        )

        return lambda_role
