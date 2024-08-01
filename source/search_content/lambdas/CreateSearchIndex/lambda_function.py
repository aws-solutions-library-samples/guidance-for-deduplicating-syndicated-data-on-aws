import boto3, os
from typing import Dict, Any
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
from dataclasses import dataclass

@dataclass
class OSSIndexItem:
    indexName: str
    indexSchema: Dict[str,Any]

index_cfg = OSSIndexItem(
            indexName = "raw",
            indexSchema = {
                "mappings": {
                    "properties": {
                        "accountid": {
                            "type": "keyword"
                        },
                        "region": {
                            "type": "keyword"
                        },
                        "CollectTime": {
                            "type": "date"
                        },
                        "tablename": {
                            "type": "text"
                        },
                        "databasename": {
                            "type": "text"
                        },
                        "owner": {
                            "type": "text"
                        },
                        "CreateTime": {
                            "type": "text"
                        },
                        "UpdateTime": {
                            "type": "text"
                        },
                        "columns": {
                            "type": "text"
                        },
                        "location": {
                            "type": "text"
                        }
                    }
                }
            }
        )

@dataclass
class OSIndexCreationParams:
    admin_role_arn: str
    external_id: str
    region: str
    host: str
    service: str = "aoss"
    port: int = 443


def dump(obj):
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))

class OSIndexCreation:

    def __init__(self, params: OSIndexCreationParams):
        self.params = params

    def main(self):
        client = self.createOSClient()
        self.createIndex(client, index_cfg)

    def createOSClient(self)->OpenSearch:
        sts_client = boto3.client("sts")
        # Call the assume_role method of the STSConnection object and pass the role ARN
        assumed_role = sts_client.assume_role(
            RoleArn=self.params.admin_role_arn,
            RoleSessionName="AssumeRoleSession1",
            ExternalId=self.params.external_id
        )

        # From the response that contains the assumed role, get the temporary credentials
        temp_credentials = assumed_role["Credentials"]

        auth = AWS4Auth(temp_credentials['AccessKeyId'],
            temp_credentials['SecretAccessKey'],
            self.params.region,
            self.params.service,
            session_token=temp_credentials['SessionToken'])

        # Create the client with SSL/TLS enabled, but hostname verification disabled.
        client = OpenSearch(
            hosts = [{'host': self.params.host, 'port': self.params.port}],
            http_auth = auth,
            verify_certs = True,
            connection_class = RequestsHttpConnection,
            use_ssl = True
        )
        return client

    def deleteIndex(self, client: OpenSearch, indexName: str):
        if client.indices.exists(index=indexName):
            client.indices.delete(index=indexName)
            print(f"Index: '{indexName}' got deleted now.")


    def createIndex(self, client: OpenSearch, indexItem: OSSIndexItem):
        if not client.indices.exists(index=indexItem.indexName):
            client.indices.create(index=indexItem.indexName, body=indexItem.indexSchema)
            print(f"Index: '{indexItem.indexName}' got created now.")
        else:
            print(f"Index: '{indexItem.indexName}' already exists")


def lambda_handler(event, context):

    region = os.environ['AWS_REGION']
    admin_role_arn = os.environ['adminRole']
    external_id = os.environ['externalId']
    host = os.environ['host'].strip().replace("https://","")
    service = os.environ['service']
    port = os.environ['port']


    print ("Region: ",region)
    print ("AdminRole: ", admin_role_arn)
    print ("SessionExternalId: ",external_id)
    print ("OpenSearch Host: ", host)
    print ("OpenSearch Port: ", port)
    print ("Service: ", service)

    params = OSIndexCreationParams(
        admin_role_arn=admin_role_arn,
        external_id=external_id,
        region=region,
        service=service,
        host=host,
        port=int(port)
    )

    OSIndexCreation(params).main()
