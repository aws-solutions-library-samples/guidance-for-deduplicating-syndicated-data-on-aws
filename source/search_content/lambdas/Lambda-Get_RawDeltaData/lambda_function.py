import json, os, boto3, botocore
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

sts_client = boto3.client("sts")
region = os.environ['AWS_REGION']
raw_host = os.environ['raw_host'].replace('https://','')
raw_index = os.environ['raw_index']
vector_host = os.environ['vector_host'].replace('https://','')
vector_index = os.environ['vector_index']
sqs_q_name = os.environ['q_name']
remote_ingest_role = os.environ['remote_ingest_role']
remote_external_id = os.environ['remote_external_id']
admin_external_id = os.environ['admin_external_id']
vector_admin_ingest_role = os.environ['vector_admin_ingest_role']


def get_recods_by_timestamp(client, acc,region, datetime, index_name):
    query = {
      "query": {
        "bool": {
          "filter": [
            {
              "range": {
                "CollectTime": {
                  "gt": datetime
                }
              }
            },
            {
              "term": {
                "accountid": acc
              }
            },
            {
              "term": {
                "region": region
              }
            }
          ]
        }
      },
    }
    response = client.search(body=query, index=index_name)
    last_docs = response['hits']['hits']
    return last_docs


def get_recods_by_region(client, acc,region, index_name):
    query = {
      "query": {
        "bool": {
          "filter": [
            {
              "term": {
                "accountid": acc
              }
            },
            {
              "term": {
                "region": region
              }
            }
          ]
        }
      },
    }
    response = client.search(body=query, index=index_name)
    last_docs = response['hits']['hits']
    return last_docs


def get_recods_by_account(client, acc, index_name):
    query = {
      "query": {
        "bool": {
          "filter": [
            {
              "term": {
                "accountid": acc
              }
            }
          ]
        }
      },
    }
    response = client.search(body=query, index=index_name)
    last_docs = response['hits']['hits']
    return last_docs


def get_lasttimestamp(account_id,region,os_client,index_name):
    query = {
      "query": {
        "bool": {
          "filter": [
            {
              "term": {
                "accountid": account_id
              }
            },
            {
              "term": {
                "region": region
              }
            }
          ]
        }
      },
      "sort": [{
        "CollectTime": {
          "order": "desc"
        }
      }],
      "size": 1
    }
    response = os_client.search(body = query,index = index_name)
    latest_doc = response['hits']['hits'][0]
    return latest_doc['_source']['CollectTime']


def get_timestamp4acct_region(client, index_name):

    regionquery = {
      "size": 0,
      "aggs": {
        "group_by_account_region": {
          "terms": {
            "field": "accountid",
            #"size": 10
          },
          "aggs": {
            "region": {
              "terms": {
                "field": "region"
              }
            }
          }
        }
      }
    }

    response = client.search(body = regionquery,index = index_name)
    print("\n",index_name,' search results:')
    accounts = response['aggregations']['group_by_account_region']['buckets']
    LastCollect = {}
    for account in accounts:
       print("Account: ",account['key'])
       LastCollect[account['key']] = {}
       regions = account['region']['buckets']
       for region in regions:
          print("  ",region['key'])
          LastCollect[account['key']][region['key']] = get_lasttimestamp(account['key'],region['key'],client,index_name)
    #print("\n")
    return LastCollect


def send2SQS(docs,q_client,queue_name):
    queue_url = q_client.get_queue_url(
        QueueName=queue_name
    )
    for doc in docs:
        # Create a new message
        response = q_client.send_message(
            QueueUrl=queue_url['QueueUrl'],
            MessageBody=json.dumps(doc)
        )
        # The response is NOT a resource, but gives you a message ID and MD5
        print("MessageId",response.get('MessageId'))
        print("MessageBody",response.get('MD5OfMessageBody'))


def getOSClient_assume(os_host: str, role: str, session_id: str):
    # Call the assume_role method of the STSConnection object and pass the role ARN
    assumed_role = sts_client.assume_role(
        RoleArn=role,
        RoleSessionName="AssumeRoleSession1",
        ExternalId=session_id
    )
    # From the response that contains the assumed role, get the temporary credentials
    temp_credentials = assumed_role["Credentials"]

    awsauth = AWS4Auth(temp_credentials['AccessKeyId'],
        temp_credentials['SecretAccessKey'],
        region,
        'aoss',
        session_token=temp_credentials['SessionToken']
    )

    os_port = 443
    os_client = OpenSearch(
        hosts = [{'host': os_host, 'port': os_port}],
        http_auth = awsauth,
        verify_certs = True,
        connection_class = RequestsHttpConnection,
        use_ssl = True
    )

    return os_client


def getOSClient(os_host: str, role: str, session_id: str):
    credentials = boto3.Session().get_credentials().get_frozen_credentials()

    awsauth = AWS4Auth(credentials.access_key,
        credentials.secret_key,
        region,
        'aoss',
        session_token=credentials.token
    )

    os_port = 443
    os_client = OpenSearch(
        hosts = [{'host': os_host, 'port': os_port}],
        http_auth = awsauth,
        verify_certs = True,
        connection_class = RequestsHttpConnection,
        use_ssl = True
    )

    return os_client



def lambda_handler(event, context):

    print ("Region",region, sep=":<", end=">")
    print ("Remote Ingest Role: ",remote_ingest_role, sep=":<", end=">\n")
    print ("Remote External Id: ",remote_external_id, sep=":<", end=">\n")
    print ("Vector Admin Ingest Role: ",vector_admin_ingest_role, sep=":<", end=">\n")
    print ("Admin External Id: ",admin_external_id, sep=":<", end=">\n")
    print ("OpenSearch Raw host URL: ",raw_host, sep=":<", end=">\n")
    print ("OpenSearch Raw Index: ", raw_index, sep=":<", end=">\n")
    print ("OpenSearch Vector Destination Index: ", vector_index, sep=":<", end=">\n")
    print ("OpenSearch Vector URL: ", vector_host, sep=":<", end=">\n")
    print ("SQS Queue name: ",sqs_q_name, sep=":<", end=">\n")

    raw_client = getOSClient_assume(os_host=raw_host, role=remote_ingest_role, session_id=remote_external_id)
    vector_client = getOSClient_assume(os_host=vector_host, role=vector_admin_ingest_role, session_id=admin_external_id)

    # Get the queue
    sqs = boto3.client('sqs')

    LastCollect_raw = get_timestamp4acct_region(raw_client, raw_index)
    LastCollect = get_timestamp4acct_region(vector_client, vector_index)

    for acc in LastCollect_raw:
        for reg in LastCollect_raw[acc]:
            print ("\n",acc,': ',reg,' - ',LastCollect_raw[acc][reg])
            docs = {}
            if acc in LastCollect:
                if reg in LastCollect[acc]:
                    print ("  Checking Last Run timestamp:")
                    raw_timestamp = LastCollect_raw[acc][reg]
                    processed_timestamp = LastCollect[acc][reg]
                    print ("   ",raw_timestamp,"<- Raw | Processed ->",processed_timestamp)
                    if raw_timestamp > processed_timestamp:
                        print("  Refresh needed")
                        docs = get_recods_by_timestamp(raw_client, acc, reg, processed_timestamp,raw_index)
                        #print ("Docs: ",docs)
                else:
                    print("  New Region")
                    docs = get_recods_by_region(raw_client, acc, reg,raw_index)
                    #print ("Docs: ",docs)
            else: # New account
                print ("  New Account")
                docs = get_recods_by_account(raw_client, acc, raw_index)
            #print ("Docs: ",json.dumps(docs))
            send2SQS(docs, sqs, sqs_q_name)
