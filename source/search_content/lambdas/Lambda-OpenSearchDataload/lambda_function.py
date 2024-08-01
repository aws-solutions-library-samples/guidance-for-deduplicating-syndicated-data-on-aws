# Required packages in the same directory:
# pip3 install -t /Users/ajancsik/PycharmProjects/listGlueTable requests_aws4auth
# pip3 install -t /Users/ajancsik/PycharmProjects/listGlueTable requests

import os
import boto3
import json
import hashlib
from datetime import datetime

from requests_aws4auth import AWS4Auth
import requests


def lambda_handler(event, context):

    region = os.environ['aws_region']
    ingest_role = os.environ['ingest_role']
    os_host = os.environ['os_host']
    os_index = os.environ['os_index']
    external_id = os.environ['external_id']
    print ("Region",region, sep=":<", end=">")
    print ("Ingest Role: ",ingest_role, sep=":<", end=">\n")
    print ("External Id: ",external_id, sep=":<", end=">\n")
    print ("OpenSearch host URL: ",os_host, sep=":<", end=">\n")
    print ("OpenSearch Index: ", os_index, sep=":<", end=">\n")

    #---- OpenSearch Server configuraton -----
    datatype = '_doc'
    headers = {"Content-Type": "application/json"}

    sts_client = boto3.client("sts")
    # Call the assume_role method of the STSConnection object and pass the role ARN
    assumed_role = sts_client.assume_role(
        RoleArn=ingest_role,
        RoleSessionName="AssumeRoleSession1",
        ExternalId=external_id
    )
    # From the response that contains the assumed role, get the temporary credentials
    temp_credentials = assumed_role["Credentials"]
    # print (temp_credentials)
    service = 'aoss'
    awsauth = AWS4Auth(temp_credentials['AccessKeyId'],
        temp_credentials['SecretAccessKey'],
        region,
        service,
        session_token=temp_credentials['SessionToken']
    )

    # url = os_host + '/' + os_index + '/' + datatype + '/' + id
    # resp = requests.get(url, auth=awsauth, headers=headers)

    # ----- Get data from Glue Catalog -----
    glue_client = boto3.client('glue')
    responseGetDatabases = glue_client.get_databases()
    databaseList = responseGetDatabases['DatabaseList']

    accnumber = sts_client.get_caller_identity()['Account']
    print ("Account Number:",accnumber)

    # ----- Load the data to OpenSearch using REST API
    tables_from_crawler=[]
    for databaseDict in databaseList:
        db_name = databaseDict['Name']
        glue_tables = glue_client.get_tables(DatabaseName=db_name, MaxResults=1000)

        for table in glue_tables['TableList']:

            tname = table['Name']
            dbname = table['DatabaseName']
            owner = table['Owner']
            ctime = table['CreateTime']
            utime = table['UpdateTime']

            columns = ""
            for column in table['StorageDescriptor']['Columns']:
                columns = columns + " "+ column["Name"]

            timestamp = int(datetime.now().timestamp()*1000)
            md5input = region + accnumber + db_name + tname
            id = hashlib.md5(md5input.encode('utf-8')).hexdigest()

            print(table['Name'])
            data = {}
            data["CollectTime"] = timestamp
            data["accountid"] = accnumber
            data["region"] = region
            data["tablename"] = table['Name']
            data["columns"] = columns
            data["databasename"] = db_name
            data["location"] = table['StorageDescriptor']['Location']
            data["owner"] = table['Owner']
            data["CreateTime"] = str(table['CreateTime'])
            data["UpdateTime"] = str(table['UpdateTime'])
            print (json.dumps(data))

            url = os_host + '/' + os_index + '/' + datatype + '/' + id
            print(url)
            r = requests.get(url, auth=awsauth, headers=headers)
            print(r.json())

            if r.status_code == 400:
                print ("New Document! ID:",id)
                rp = requests.put(url, auth=awsauth, data=json.dumps(data), headers=headers)
                print(rp.json())
            elif r.status_code == 404:
                if '_index' in r.json():
                    print ("New Document! ID:",id)
                    rp = requests.put(url, auth=awsauth, data=json.dumps(data), headers=headers)
                    print(rp)
            elif r.status_code == 200:
                print ("Document found! ID:",id)
                if r.json()['_source']['columns'] != columns:
                    print ("Some change happened, send update to OpenSearch")
                    rp = requests.put(url, auth=awsauth, data=json.dumps(data), headers=headers)
                    print (rp)

            else:
                print("Something unexpected happened", id)
                print(r.status_code)
                print(r.json())

            # r = requests.put(url, auth=awsauth, data=json.dumps(data), headers=headers)
            #print (r)
