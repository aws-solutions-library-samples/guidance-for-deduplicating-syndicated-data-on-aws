import json, os, boto3, requests
from requests_aws4auth import AWS4Auth

sts_client = boto3.client("sts")
region = os.environ['AWS_REGION']
vector_host = os.environ['vector_host']
vector_index = os.environ['vector_index']
kmean_endpoint = os.environ['kmean_endpoint']
admin_external_id = os.environ['admin_external_id']
vector_admin_ingest_role = os.environ['vector_admin_ingest_role']

def getAuth_assume(os_host: str, role: str, session_id: str):
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

    # os_port = 443
    # os_client = OpenSearch(
    #     hosts = [{'host': os_host, 'port': os_port}],
    #     http_auth = awsauth,
    #     verify_certs = True,
    #     connection_class = RequestsHttpConnection,
    #     use_ssl = True
    # )

    return awsauth


def sentence_to_vector(column):
    #print("raw_input_len:", len(raw_inputs))
    vectors = []
    bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # Replace with your desired region
    )

    #for column in raw_inputs:
    print ("column Name:",column)
    body = json.dumps({"inputText": column})
        # The actual call to retrieve a response from the model
    response = bedrock_runtime.invoke_model(
       body=body,
       modelId="amazon.titan-embed-text-v1",  # Replace with your model ID
       accept='application/json',
       contentType='application/json'
    )
    response_body = json.loads(response.get('body').read())
    vectors.append(response_body['embedding'])
    return (vectors)

def get_kmeans_labels(vectors):
    labels = []
    runtime= boto3.client('runtime.sagemaker')
    ENDPOINT_NAME = kmean_endpoint
    #for vector in vectors:
    vector_string = str(vectors[0])[1:-1]
    #print(vector_string)
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,ContentType='text/csv',Body=vector_string)
    result = json.loads(response['Body'].read().decode())
    labels.append(result['predictions'][0]['closest_cluster'])
    #print(result)
    return labels


def lambda_handler(event, context):

    print ("Region",region, sep=":<", end=">")
    print ("Vector Admin Ingest Role: ",vector_admin_ingest_role, sep=":<", end=">\n")
    print ("Admin External Id: ",admin_external_id, sep=":<", end=">\n")
    print ("OpenSearch Vector Destination Index: ", vector_index, sep=":<", end=">\n")
    print ("OpenSearch Vector URL: ", vector_host, sep=":<", end=">\n")
    print ("K-means Endpoint: ", kmean_endpoint, sep=":<", end=">\n")

    vector_auth = getAuth_assume(os_host=vector_host, role=vector_admin_ingest_role, session_id=admin_external_id)

    headers = {"Content-Type": "application/json"}
    datatype = '_doc'

    for record in event['Records']:

        payload = json.loads(record["body"])
        print ("Payload recieved!")
        print(record)
        print(payload)

        destdata = payload["_source"]
        id = payload["_id"]
        destdata["id_search"] = id
        print(destdata["columns"])

        # ---- Get vectors from Bedrock Titan model ---
        vector_sentences = sentence_to_vector(destdata["columns"])
        print ("Vector sentence:", vector_sentences)
        destdata["columns_vector"] = vector_sentences[0]

        # ---- Get K-Mean Labels from Deployed Sagemaker model ----
        kmean_labels = get_kmeans_labels(vector_sentences)
        print ("K-Mean labels:" , kmean_labels)
        destdata["K-meanLabel"] = kmean_labels

        # ---- Store the Enreached data to Opensearch vector index ----
        url = vector_host + '/' + vector_index + '/' + datatype
        print(url)
        rp = requests.post(url, auth=vector_auth, data=json.dumps(destdata), headers=headers)
        print(rp)
        #print (json.dumps(destdata))
        #put_openseach(opensearch_c, os_dest_index, df_all)

    return     {
        'statusCode': 200,
        'body': 'w'
    }
