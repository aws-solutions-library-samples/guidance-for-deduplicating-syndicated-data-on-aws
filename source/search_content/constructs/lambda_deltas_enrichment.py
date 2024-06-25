from aws_cdk import (
    CfnParameter,
    Duration,
    Size,
    Stack,
    aws_iam as _iam,
    aws_lambda as _lambda

)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct
from typing import Dict, List, Any
import json, subprocess

from search_content.config import OSS, LambdaLayer, LambdaDeltasEnrichmentCfg
from search_content.constructs.sqs_construct import ContentQueue


class LambdaDeltasEnrichment(Construct):

    memory_size = 2048

    def __init__(self, scope: Construct, construct_id: str,
        layers: List[_lambda.LayerVersion],
        parameters: Dict[str, Any],
        enrichRole: _iam.Role) -> None:
        super().__init__(scope, construct_id)

        self._layers = layers
        self.parameters = parameters
        self.region = Stack.of(self).region
        self.account = Stack.of(self).account

        self.deltasFn = self.buildLambdaEnrichment(enrichRole)


    def buildLambdaEnrichment(self, lambda_role: _iam.Role)->_lambda.Function:

        deltas_function = _lambda.Function(
            self, 'Lambda',
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset(LambdaDeltasEnrichmentCfg.ASSET_PATH),
            handler=LambdaDeltasEnrichmentCfg.HANDLER,
            function_name=LambdaDeltasEnrichmentCfg.NAME,
            environment={
                'env': 'dev',
                'vector_host': self.parameters['vector_collection_endpoint'],
                'vector_index':self.parameters['vectorIndex'].value_as_string,
                'vector_admin_ingest_role': f'arn:aws:iam::{self.account}:role/vectorsearch{OSS.ADMIN_ACCESS_ROLE_NAME}Normal',
                'admin_external_id': OSS.ADMIN_EXTERNAL_ID
            },
            layers=self._layers,
            timeout=LambdaDeltasEnrichmentCfg.TIME_OUT,
            memory_size=128,
            max_event_age=Duration.seconds(21600),
            retry_attempts=2,
            ephemeral_storage_size=Size.mebibytes(512),
            architecture=_lambda.Architecture.ARM_64,
            role=lambda_role    # type: ignore
        )

        return deltas_function
