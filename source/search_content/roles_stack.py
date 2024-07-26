from typing_extensions import Dict
from aws_cdk import (
    CfnParameter,
    Stack,
    Aspects,
    aws_iam as _iam
)
from cdk_nag import ( AwsSolutionsChecks, NagSuppressions )
from constructs import Construct
from search_content.config import OSS, LambdaDataLoadCfg, LambdaDelta2QueueCfg, LambdaDeltasEnrichmentCfg, Queue


class InitRolesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.roles = {
            "data_load_role": self.buildLambdaDataloadRole(),
            "data_2_q_role": self.buildLambdaDelta2QRole(),
            "enrichment_role": self.buildLambdaEnrichmentRole()
        }

        Aspects.of(self).add(AwsSolutionsChecks())
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-IAM4", "reason":"AWSLambdaBasicExecutionRole AWS managed policy is Required."}])
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-IAM5", "reason":"Wildcards are necessary here."}])


    def buildLambdaDataloadRole(self)->_iam.Role:
        lambda_role = _iam.Role(
            self, 'DataLoadRole',
            role_name=LambdaDataLoadCfg.INGESTION_ROLE_NAME,
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com')   # type: ignore
        )

        lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            'service-role/AWSLambdaBasicExecutionRole'
        ))

        lambda_role.attach_inline_policy(
            _iam.Policy(
                self, 'DataLoadPolicy',
                statements=[
                    _iam.PolicyStatement(
                        actions=[
                            'glue:GetDatabases',
                            'glue:GetTables'
                        ],
                        resources=[f'arn:aws:glue:{self.region}:{self.account}:*']
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'sts:AssumeRole'
                        ],
                        resources=[f'arn:aws:iam::*:role/{OSS.REMOTE_ACCESS_ROLE_NAME}']
                    )
                ]
            )
        )

        return lambda_role


    def buildLambdaDelta2QRole(self)->_iam.Role:
        lambda_role = _iam.Role(
            self, 'Delta2QRole',
            role_name=LambdaDelta2QueueCfg.INGESTION_ROLE_NAME,
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com')   # type: ignore
        )

        lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            'service-role/AWSLambdaBasicExecutionRole'
        ))

        lambda_role.attach_inline_policy(
            _iam.Policy(
                self, 'Delta2QPolicy',
                statements=[
                    _iam.PolicyStatement(
                        actions=[
                            'ssm:Describe*',
                            'ssm:Get*',
                            'ssm:List*'
                        ],
                        resources=['*']
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'sqs:*'
                        ],
                        resources=[f"arn:aws:sqs:{self.region}:{self.account}:{Queue.NAME}"]
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'sts:AssumeRole'
                        ],
                        resources=[f'arn:aws:iam::{self.account}:role/{OSS.REMOTE_ACCESS_ROLE_NAME}']
                    ),
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
                            f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/{LambdaDelta2QueueCfg.NAME}:*'
                        ]
                    ),
                ]
            )
        )

        return lambda_role

    def buildLambdaEnrichmentRole(self)->_iam.Role:
        lambda_role = _iam.Role(
            self, 'EnrichmentRole',
            role_name=LambdaDeltasEnrichmentCfg.INGESTION_ROLE_NAME,
            assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com')   # type: ignore
        )

        lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
            'service-role/AWSLambdaBasicExecutionRole'
        ))

        lambda_role.attach_inline_policy(
            _iam.Policy(
                self, 'EnrichmentPolicy',
                statements=[
                    _iam.PolicyStatement(
                        actions=[
                            'bedrock:InvokeModel',
                            'sagemaker:InvokeEndpoint'
                        ],
                        resources=[
                            f'arn:aws:sagemaker:*:{self.account}:endpoint/*',
                            'arn:aws:bedrock:*::foundation-model/*'
                        ]
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'ssm:Describe*',
                            'ssm:Get*',
                            'ssm:List*'
                        ],
                        resources=['*']
                    ),
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
                            f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/{LambdaDeltasEnrichmentCfg.NAME}:*'
                        ]
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'sts:AssumeRole'
                        ],
                        resources=[f'arn:aws:iam::{self.account}:role/{OSS.ADMIN_ACCESS_ROLE_NAME}']
                    ),
                ]
            )
        )
        return lambda_role
