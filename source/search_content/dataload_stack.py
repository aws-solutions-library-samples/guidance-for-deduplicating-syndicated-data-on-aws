from aws_cdk import (
    CfnParameter,
    Stack,
    Aspects,
    aws_iam as _iam,
)
from cdk_nag import ( AwsSolutionsChecks, NagSuppressions )
from constructs import Construct
import subprocess

from search_content.constructs.lambda_open_search_data_load import LambdaDataload

class DataLoadStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, role:_iam.Role ) -> None:
        super().__init__(scope, construct_id, description="Guidance for Deduplicating Syndicated data on AWS (SO9509)")

        self.defineParameters()
        dataloadFn = LambdaDataload(self, "dataload", self.parameters, role)
        Aspects.of(self).add(AwsSolutionsChecks())
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-L1", "reason":"Code was tested with python 3.11"}])


    def defineParameters(self):
        region = CfnParameter(self, "region", type="String",
            description="Glue Data Catalog AWS region")

        ingestRole = CfnParameter(self, "ingestRole", type="String",
            description="Open Search Ingest Role")

        osHost = CfnParameter(self, "osHost", type="String",
            description="Open Search Server Host URL with https://",)

        osIndex = CfnParameter(self, "osIndex", type="String",
            description="Open Search Server Index for raw dataload",)

        externalId = CfnParameter(self, "externalId", type="String",
            description="Open Search Server Index for raw dataload",)

        self.parameters = {
            'awsRegion': region,
            'ingestRole': ingestRole,
            'externalId': externalId,
            'osHost': osHost,
            'osIndex': osIndex
        }
