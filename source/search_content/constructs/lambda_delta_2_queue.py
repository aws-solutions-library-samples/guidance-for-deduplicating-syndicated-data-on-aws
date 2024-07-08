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
from typing import List, Dict, Any
import json, subprocess

from search_content.config import OSS, LambdaLayer, LambdaDelta2QueueCfg, Queue
from search_content.constructs.sqs_construct import ContentQueue


class LambdaDelta2Queue(Construct):

    def __init__(self, scope: Construct, construct_id: str,
        layers: List[_lambda.LayerVersion],
        queue_arn: str,
        parameters: Dict[str, Any],
        delta2qRole: _iam.Role) -> None:
        super().__init__(scope, construct_id)

        self._layers = layers
        self.parameters = parameters
        self.region = Stack.of(self).region
        self.account = Stack.of(self).account

        self.deltasFn = self.buildLambdaDelta2Q(delta2qRole)


    def buildLambdaDelta2Q(self, lambda_role: _iam.Role)->_lambda.Function:

        deltas_function = _lambda.Function(
            self, 'Lambda',
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset(LambdaDelta2QueueCfg.ASSET_PATH),
            handler=LambdaDelta2QueueCfg.HANDLER,
            function_name=LambdaDelta2QueueCfg.NAME,
            environment={
                'env': 'dev',
                'raw_host': self.parameters['search_collection_endpoint'],
                'raw_index': self.parameters['searchIndex'].value_as_string,
                'vector_host': self.parameters['vector_collection_endpoint'],
                'vector_index': self.parameters['vectorIndex'].value_as_string,
                'q_name': Queue.NAME,
                'remote_ingest_role': f'arn:aws:iam::{self.account}:role/{OSS.REMOTE_ACCESS_ROLE_NAME}',
                'remote_external_id': OSS.REMOTE_EXTERNAL_ID,
                'vector_admin_ingest_role': f'arn:aws:iam::{self.account}:role/vectorsearch{OSS.ADMIN_ACCESS_ROLE_NAME}Normal',
                'admin_external_id': OSS.ADMIN_EXTERNAL_ID
            },
            layers=self._layers,
            timeout=LambdaDelta2QueueCfg.TIME_OUT,
            memory_size=128,
            max_event_age=Duration.seconds(21600),
            retry_attempts=2,
            ephemeral_storage_size=Size.mebibytes(512),
            architecture=_lambda.Architecture.ARM_64,
            role=lambda_role  # type: ignore
        )

        return deltas_function
