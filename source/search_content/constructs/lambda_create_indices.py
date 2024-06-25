from aws_cdk import (
    CfnParameter,
    Duration,
    Size,
    Stack,
    aws_iam as _iam,
    aws_lambda as _lambda

)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from aws_cdk.aws_opensearchserverless import CfnCollection
from constructs import Construct
from typing import List, Dict, Any
import json, subprocess

from search_content.config import OSS
from search_content.constructs.build_layer import BuildLambdaLayer
from search_content.constructs.collection import OSCollection
from search_content.constructs.sqs_construct import ContentQueue
import aws_cdk.triggers as triggers
from dataclasses import dataclass

from search_content.lambdas.CreateSearchIndex.lambda_function import OSIndexCreationParams
from search_content.constructs.opensearch import OpenSearchConstruct

@dataclass
class LambdaCreateIndicesParams:
    constructDependencies: List[Construct]
    creationParams: OSIndexCreationParams

@dataclass
class LambdaTriggerCfg:
    asset_path: str
    handler: str
    name: str
    timeout: Duration



class LambdaTriggers:
    searchCfg =  LambdaTriggerCfg(
        asset_path= 'search_content/lambdas/CreateSearchIndex',
        handler= 'lambda_function.lambda_handler',
        name= 'createSearchIndex',
        timeout= Duration.seconds(10)
    )

    vectorCfg =  LambdaTriggerCfg(
        asset_path= 'search_content/lambdas/CreateVectorIndex',
        handler= 'lambda_function.lambda_handler',
        name= 'createVectorIndex',
        timeout= Duration.seconds(10)
    )

class LambdaCreateIndices(Construct):

    def __init__(self, scope: Construct, construct_id: str,
        oss: OpenSearchConstruct, role_admin_init: _iam.Role
        # params: LambdaCreateIndicesParams
    ) -> None:
        super().__init__(scope, construct_id)
        self.region = Stack.of(self).region
        self.account = Stack.of(self).account
        self.oss = oss

        self.layer = BuildLambdaLayer(scope, "LambdaLayer").layer

        self.createTriggerFunction(self.oss.search_collection, LambdaTriggers.searchCfg, role_admin_init)
        self.createTriggerFunction(self.oss.vector_collection, LambdaTriggers.vectorCfg, role_admin_init)


    def createTriggerFunction(self, collection: OSCollection, cfg: LambdaTriggerCfg, role_admin_init: _iam.Role):
        params = LambdaCreateIndicesParams(
            constructDependencies=[self.oss],
            creationParams=OSIndexCreationParams(
                admin_role_arn=collection.admin_role_init,
                external_id=OSS.ADMIN_EXTERNAL_ID,
                region=self.region,
                host=collection.collection.attr_collection_endpoint
            )
        )

        triggers.TriggerFunction(self, f"{cfg.name}-Trigger",
            execute_after=params.constructDependencies,
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler=cfg.handler,
            code=_lambda.Code.from_asset(cfg.asset_path, deploy_time=True),
            architecture=_lambda.Architecture.ARM_64,
            function_name=cfg.name,
            layers=[self.layer],
            timeout=cfg.timeout,
            role=role_admin_init, # type: ignore
            memory_size=128,
            retry_attempts=0,
            environment={
                'env': 'dev',
                'adminRole':  params.creationParams.admin_role_arn,
                'host': params.creationParams.host,
                'externalId': params.creationParams.external_id,
                'service': "aoss",
                'port': "443",
            },
        )


    # def getTriggerRole(self)->_iam.Role:
    #     lambda_role = _iam.Role(
    #         self, 'Role',
    #         assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com')   # type: ignore
    #     )

    #     lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(
    #         'service-role/AWSLambdaBasicExecutionRole'
    #     ))

    #     lambda_role.attach_inline_policy(
    #         _iam.Policy(
    #             self, 'InlinePolicy',
    #             statements=[
    #                 _iam.PolicyStatement(
    #                     actions=[
    #                         'ssm:Describe*',
    #                         'ssm:Get*',
    #                         'ssm:List*'
    #                     ],
    #                     resources=['*']
    #                 ),
    #                 _iam.PolicyStatement(
    #                     actions=["logs:CreateLogGroup"],
    #                     resources=[
    #                         f'arn:aws:logs:{self.region}:{self.account}:*'
    #                     ]
    #                 ),
    #                 _iam.PolicyStatement(
    #                     actions=[
    #                         'logs:CreateLogStream',
    #                         'logs:PutLogEvents'
    #                     ],
    #                     resources=[
    #                         f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/{LambdaCfg.NAME}:*'
    #                     ]
    #                 ),
    #             ]
    #         )
    #     )
    #     return lambda_role
