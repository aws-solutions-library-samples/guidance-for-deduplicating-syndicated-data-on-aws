from aws_cdk import (
    # CfnParameter,
    # Duration,
    # Size,
    Stack,
    # aws_iam as _iam,
    aws_lambda as _lambda

)
from constructs import Construct
import os, subprocess

from search_content.config import LambdaLayer

class BuildLambdaLayer(Construct):

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.region = Stack.of(self).region
        self.account = Stack.of(self).account

        self.layer = self.buildLayer()

    def buildLayer(self)->_lambda.LayerVersion:
        dest_path = f'{LambdaLayer.ASSET_PATH}/python/lib/python3.11/site-packages'
        if not os.path.isdir(dest_path):
            subprocess.call(['pip', 'install',
                    '-t', dest_path,
                    '-r', f'{LambdaLayer.ASSET_PATH}/requirements.txt',
                    '--platform', 'manylinux2014_x86_64', '--only-binary=:all:',
                    '--upgrade'])

        layer = _lambda.LayerVersion(scope=self,
                                    id=LambdaLayer.NAME,
                                    code=_lambda.Code.from_asset(LambdaLayer.ASSET_PATH),
                                    compatible_runtimes=[_lambda.Runtime.PYTHON_3_11])

        return layer
