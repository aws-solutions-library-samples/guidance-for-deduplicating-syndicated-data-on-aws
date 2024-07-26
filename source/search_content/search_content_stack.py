from aws_cdk import (
    aws_iam as _iam,
    Aspects
)
from cdk_nag import ( AwsSolutionsChecks, NagSuppressions )
from typing import List, Dict
from aws_cdk import CfnParameter, Stack, Fn, Token
from constructs import Construct
from search_content.config import OSS
from search_content.constructs.lambda_create_indices import LambdaCreateIndices
from search_content.constructs.opensearch import OpenSearchConstruct
from search_content.constructs.lambda_admin_init_role import RoleAdminInit

class SearchContentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, delta2qRole: _iam.Role) -> None:
        super().__init__(scope, construct_id)

        self.role_admin_init = RoleAdminInit(self, "RoleAdminInit").role_admin_init
        self.defineParameters(self.role_admin_init.role_arn, delta2qRole.role_arn)
        self.oss = OpenSearchConstruct(self, "oss", self.parameters)
        self.search_collection_endpoint = self.oss.search_collection.collection.attr_collection_endpoint

        trigger = LambdaCreateIndices(self, "LambdaCreateIndices", self.oss, self.role_admin_init)

        self.layer = trigger.layer
        Aspects.of(self).add(AwsSolutionsChecks())
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-IAM4", "reason":"AWSLambdaBasicExecutionRole AWS managed policy is Required."}])
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-IAM5", "reason":"Wildcards are necessary here."}])
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-L1", "reason":"Code was tested with python 3.11"}])
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-SQS3", "reason":"dead-letter queue not configured as this is not meant to be used for production."}])


    def defineParameters(self, role_admin_init_arn: str, delta2q_arn: str):
        ext = CfnParameter(self, "EXPRINCIPALS",
            type="CommaDelimitedList",
            description="External principals to trust"
        )

        adm = CfnParameter(self, "ADPRINCIPALS",
            type="CommaDelimitedList",
            description="Admin principals to trust"
        )

        self.parameters: Dict[str,List[str]] = {
            'EXTERNAL_PRINCIPALS': ext.value_as_list,
            'ADMIN_PRINCIPALS': adm.value_as_list,
            'additional_admin_vector_principals': [delta2q_arn],
            'admin_init_role_arns': [role_admin_init_arn]
        }
