from aws_cdk import (
    CfnParameter,
    Duration,
    Size,
    Stack,
    Aspects,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_sqs as _sqs
)
from cdk_nag import ( AwsSolutionsChecks, NagSuppressions )
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct
from typing import List, Dict
import json, subprocess, os

from opensearchpy.client import OpenSearch

from search_content.config import Queue
from search_content.constructs.lambda_delta_2_queue import LambdaDelta2Queue
from search_content.constructs.lambda_deltas_enrichment import LambdaDeltasEnrichment
from search_content.constructs.opensearch import OpenSearchConstruct
from search_content.constructs.sqs_construct import ContentQueue


class LambdasStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
        oss: OpenSearchConstruct,
        layers: List[_lambda.LayerVersion],
        roles: Dict[str, _iam.Role]) -> None:
        super().__init__(scope, construct_id)

        self.defineParameters(oss)

        queue = ContentQueue(self, "contentQueue")
        deltas_enrich = LambdaDeltasEnrichment(self, "deltas", layers, self.parameters, roles['enrichment_role']).deltasFn
        # deltas_enrich.add_event_source(SqsEventSource(queue.queue))
        deltas_enrich.add_event_source(SqsEventSource(
            ### This avoids cyclic reference in dependencies
            _sqs.Queue.from_queue_arn(self, "QRef", f"arn:aws:sqs:{self.region}:{self.account}:{Queue.NAME}")
        ))


        delta2Queue = LambdaDelta2Queue(self, "delta2Q", layers, queue.arn, self.parameters, roles['data_2_q_role'])

        Aspects.of(self).add(AwsSolutionsChecks())
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-L1", "reason":"Code was tested with python 3.11"}])
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-SQS3", "reason":"dead-letter queue not configured as this is not meant to be used for production."}])
        NagSuppressions.add_stack_suppressions(self, [{"id":"AwsSolutions-SQS4", "reason":"Queue only usable within the AWS Account."}])


    def defineParameters(self, oss: OpenSearchConstruct):

        searchIndex = CfnParameter(self, "searchIndex", type="String",
            description="Open Search raw Index for dataload",
            default="raw")

        vectorIndex = CfnParameter(self, "vectorIndex", type="String",
            description="Open Search Vector Index",
            default="fultable_dedup")

        kmeanEndpoint = CfnParameter(self, "kmeanEndpoint", type="String",
            description="k-mean SageMaker endpoint")

        self.parameters = {
            'search_collection_endpoint': oss.search_collection.collection.attr_collection_endpoint,
            'vector_collection_endpoint': oss.vector_collection.collection.attr_collection_endpoint,
            'kmean_endpoint': kmeanEndpoint,
            'searchIndex': searchIndex,
            'vectorIndex': vectorIndex,
        }
