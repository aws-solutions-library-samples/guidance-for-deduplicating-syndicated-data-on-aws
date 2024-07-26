from typing_extensions import Dict
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
from typing import List
import json, subprocess, os

from search_content.config import OSS, LambdaDataLoadCfg
from search_content.constructs.sqs_construct import ContentQueue


class LambdaDataload(Construct):

    def __init__(self, scope: Construct, construct_id: str,
        parameters: Dict[str,CfnParameter],
        role: _iam.Role) -> None:
        super().__init__(scope, construct_id)

        self.region = Stack.of(self).region
        self.account = Stack.of(self).account
        self.parameters = parameters

        if not os.path.isdir(f'{LambdaDataLoadCfg.ASSET_PATH}/boto3'):
            subprocess.call(
                ['pip', 'install', '-t', f'{LambdaDataLoadCfg.ASSET_PATH}', '-r',
                f'{LambdaDataLoadCfg.ASSET_PATH}/requirements.txt', '--platform', 'manylinux2014_x86_64', '--only-binary=:all:',
                '--upgrade'])

        self.dataloadFn = self.buildLambdaDataload(role)


    def buildLambdaDataload(self, lambda_role: _iam.Role)->_lambda.Function:

        deltas_function = _lambda.Function(
            self, 'Lambda',
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset(LambdaDataLoadCfg.ASSET_PATH),
            handler=LambdaDataLoadCfg.HANDLER,
            function_name=LambdaDataLoadCfg.NAME,
            environment={
                'os_host': self.parameters['osHost'].value_as_string,
                'os_index': self.parameters['osIndex'].value_as_string,
                'aws_region': self.parameters['awsRegion'].value_as_string,
                'ingest_role': self.parameters['ingestRole'].value_as_string,
                'external_id': self.parameters['externalId'].value_as_string,
            },
            timeout=LambdaDataLoadCfg.TIME_OUT,
            memory_size=128,
            max_event_age=Duration.seconds(21600),
            retry_attempts=2,
            ephemeral_storage_size=Size.mebibytes(512),
            architecture=_lambda.Architecture.ARM_64,
            role=lambda_role    # type: ignore
        )

        return deltas_function
