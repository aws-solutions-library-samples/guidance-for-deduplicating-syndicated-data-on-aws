from dataclasses import dataclass
from aws_cdk import Duration
from typing import Dict, Any
from dataclasses import dataclass


class Queue:
    VISIBILITY_TIME_OUT = Duration.seconds(120)
    RETENTION = Duration.days(3)
    NAME = 'contentQ'

class LambdaDeltasEnrichmentCfg:
    ASSET_PATH = 'search_content/lambdas/Lambda-deltasqs2enreachment'
    HANDLER = 'lambda_function.lambda_handler'
    NAME = 'deltaq2enreachment'
    INGESTION_ROLE_NAME = 'LambdasStack-InternalEnrichmentRole'
    TIME_OUT = Queue.VISIBILITY_TIME_OUT.minus(Duration.seconds(10))


class LambdaDelta2QueueCfg:
    ASSET_PATH = 'search_content/lambdas/Lambda-Get_RawDeltaData'
    HANDLER = 'lambda_function.lambda_handler'
    NAME = 'delta2q'
    INGESTION_ROLE_NAME = 'LambdasStack-InternalIngestionRole'
    TIME_OUT = Queue.VISIBILITY_TIME_OUT.minus(Duration.seconds(10))


class LambdaDataLoadCfg:
    ASSET_PATH = 'search_content/lambdas/Lambda-OpenSearchDataload'
    HANDLER = 'lambda_function.lambda_handler'
    NAME = 'OpenSearchDataload'
    INGESTION_ROLE_NAME = 'DataLoadStack-ExternalIngestionRole'
    TIME_OUT = Duration.seconds(600)


class LambdaLayer:
    ASSET_PATH = 'search_content/lambdas/Lambda_layer'
    NAME = 'panda-opesearch-request-bedrock'


@dataclass
class OSS_COLLECTION:
    name: str
    type: str
    isRemoteEnabled: bool


@dataclass
class OSS_COLLECTIONS:
    search: OSS_COLLECTION
    vector: OSS_COLLECTION


class OSS:
    COLLECTIONS = OSS_COLLECTIONS(
        search = OSS_COLLECTION(
            name= 'searchable-content',
            type= 'SEARCH',
            isRemoteEnabled=True
        ),
        vector = OSS_COLLECTION(
            name= 'vector-content',
            type= 'VECTORSEARCH',
            isRemoteEnabled=False
        )
    )
    ADMIN_ACCESS_ROLE_NAME = 'admin-searchable-content'
    REMOTE_ACCESS_ROLE_NAME = 'ingest-searchable-content'
    ADMIN_EXTERNAL_ID = 'Word2+Zr0-1lNrU7G=WraPPer'
    REMOTE_EXTERNAL_ID = 'ValorExternou8n4Fh4hFSauHbsm'
