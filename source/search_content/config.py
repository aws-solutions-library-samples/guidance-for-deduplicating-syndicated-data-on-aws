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
#     AWS_PRINCIPALS = [
#         "123456789012",
#         "987654321098"
#     ]

# @dataclass
# class OSSIndexItem:
#     indexName: str
#     indexSchema: Dict[str,Any]

# class OSSIndex:
#     INDEX_LIST = [
#         OSSIndexItem(
#             indexName = "raw",
#             indexSchema = {
#                 "mappings": {
#                     "properties": {
#                     "accountid": {
#                         "type": "keyword"
#                     },
#                     "region": {
#                         "type": "keyword"
#                     },
#                     "CollectTime": {
#                         "type": "date"
#                     },
#                     "tablename": {
#                         "type": "text"
#                     },
#                     "databasename": {
#                         "type": "text"
#                     },
#                     "owner": {
#                         "type": "text"
#                     },
#                     "CreateTime": {
#                         "type": "text"
#                     },
#                     "UpdateTime": {
#                         "type": "text"
#                     },
#                     "columns": {
#                         "type": "text"
#                     },
#                     "location": {
#                         "type": "text"
#                     }
#                     }
#                 }
#             }
#         ),
#         OSSIndexItem(
#             indexName = "fultable_dedup",
#             indexSchema = {
#                 "settings": {
#                     "index.knn": True,
#                     "index.knn.space_type": "cosinesimil",
#                     "analysis": {
#                     "analyzer": {
#                         "default": {
#                         "type": "standard",
#                         "stopwords": "_english_"
#                         }
#                     }
#                     }
#                 },
#                 "mappings": {
#                     "properties": {
#                         "columns_vector": {
#                             "type": "knn_vector",
#                             "dimension": 1536,
#                             "store": True
#                         },
#                         "accountid": {
#                             "type": "keyword",
#                             "store": True
#                         },
#                         "region": {
#                             "type": "keyword",
#                             "store": True
#                         },
#                         "CollectTime": {
#                             "type": "date",
#                             "store": True
#                         },
#                         "tablename": {
#                             "type": "text",
#                             "store": True
#                         },
#                         "databasename": {
#                             "type": "text",
#                             "store": True
#                         },
#                         "owner": {
#                             "type": "text",
#                             "store": True
#                         },
#                         "CreateTime": {
#                             "type": "text",
#                             "store": True
#                         },
#                         "UpdateTime": {
#                             "type": "text",
#                             "store": True
#                         },
#                         "columns": {
#                             "type": "text",
#                             "store": True
#                         },
#                         "location": {
#                             "type": "text",
#                             "store": True
#                         },
#                         "K-meanLabel": {
#                             "type": "integer",
#                             "store": True
#                         }
#                     }
#                 }
#             }
#         ),
#     ]
