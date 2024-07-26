from aws_cdk import (
    CfnParameter,
    aws_iam as _iam,
    Stack,
)
from aws_cdk.aws_opensearchserverless import (
    CfnCollection,
    CfnAccessPolicy,
    CfnSecurityPolicy,
    CfnVpcEndpoint
)
from aws_cdk.aws_ec2 import  (
    IpProtocol, SubnetType, Vpc,
    IpAddresses, SubnetConfiguration
)
from constructs import Construct
from typing import Dict, List
import json
from search_content.config import OSS, OSS_COLLECTION, OSS_COLLECTIONS, LambdaDelta2QueueCfg
from search_content.constructs.collection import OSCollection


class OpenSearchConstruct(Construct):

    def __init__(self, scope: "Construct", contruct_id: str,
        parameters: Dict[str, List[str]]) -> None:
        super().__init__(scope, contruct_id)

        self.search_collection = OSCollection(self, "searchCol",
            parameters=parameters,
            collection_cfg=OSS.COLLECTIONS.search
        )

        self.vector_collection = OSCollection(self, "vectorCol",
            parameters=parameters,
            collection_cfg=OSS.COLLECTIONS.vector,
            addAdditionalPrincipals=True
        )
