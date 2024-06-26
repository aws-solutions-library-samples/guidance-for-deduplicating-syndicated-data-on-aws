# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project. The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory. To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation

Enjoy!

## 00. cdk bootstrap - *Main* & *Secondary* accounts

Set AWS credentials for the **Account** where the infrastructure will be deployed and run **cdk bootstrap**

```shell
cdk bootstrap
```

## 01. RolesStack Deployment - *Main* & *Secondary* accounts

This stack contains lambda roles that will be neccesary in other stacks. Without this other stacks will fail to deploy or not work correctly.

```shell
cdk deploy RolesStack
```

## 02. SearchContentStack Deployment - *Main* account only

* EXPRINCIPALS: Contains a comma separated list of *Principal* arn's, 3 from the *Main* account that will be used to setup the pipeline and zero or more
 in other AWS accounts (not the *Main* account) that will be authorized to push data into the system using `OpenSearchDataload` lambda deployed with the *DataloadStack*.

Template:
--parameters SearchContentStack:EXPRINCIPALS="<main roles - 3>,<secondary roles - n>"

1. main roles: Only these 3 roles provided here with *Main Account Number* changed
`arn:aws:sts::{Main Account number}:assumed-role/DataLoadStack-ExternalIngestionRole/OpenSearchDataload,arn:aws:sts::{Main Account Number}:assumed-role/LambdasStack-InternalIngestionRole/delta2q,arn:aws:sts::{Main Account Number}:assumed-role/LambdasStack-InternalEnrichmentRole/deltaq2enreachment`

2. secondary roles: As many copies of this unique role per *Secondary* Account you want to use, change `Secondary Account Number` accordingly and separate each copy with a comma.
`arn:aws:sts::{Secondary Account Number}:assumed-role/DataLoadStack-ExternalIngestionRole/OpenSearchDataload`

* ADPRINCIPALS: Contains a comma separated list of *Principals* in *Main* AWS account that will be admins of the system.

Template:
--parameters SearchContentStack:ADPRINCIPALS="<main roles: 3>

```shell
cdk deploy SearchContentStack \
--parameters SearchContentStack:EXPRINCIPALS="arn:aws:sts::XXXX:assumed-role/DataLoadStack-ExternalIngestionRole/OpenSearchDataload,arn:aws:sts::YYYY:assumed-role/DataLoadStack-ExternalIngestionRole/OpenSearchDataload" \
--parameters SearchContentStack:ADPRINCIPALS="arn:aws:sts::YYYY:assumed-role/Admin/<user>,arn:aws:sts::YYYY:assumed-role/AmazonSageMakerServiceCatalogProductsUseRole/SageMaker"

```


## 03. LambdasStack Deployment - *Main* account only

* searchIndex: is the name of the search index deployed in *SearchContentStack*. Default: `raw`

* vectorIndex: is the name of the vector index deployed in *SearchContentStack*. Default: `fultable_dedup`

See `search_content/config.py` for other default details.

```shell
cdk deploy LambdasStack \
--parameters LambdasStack:searchIndex=raw \
--parameters LambdasStack:vectorIndex=fultable_dedup

```

## 04. DataLoadStack Deployment - *Main* & *Secondary* accounts

This stack will be deployed in each AWS Account authorized to push data into the system. Deployment must be executed on each account independently by following steps: *00, 01 and 04 of this guide*.


* region: The AWS Region where the data will be collected.
* ingestRole: The arn of the authorized role to be used to push data. Use the pattern below with the appropriate AWS account used an *Main*.
* osHost: The OpenSearch *Search* Collection host where the data will be pushed. Go to CloudFormation -> SearchContentStack -> Outputs to get it.
* osIndex: The OpenSearch index name where the data will be pushed.
* externalId: The security Id necessary to push data into OpenSearch. This value has been hardcoded in `search_content/config.py` and should be changed.

```shell
cdk deploy DataLoadStack \
--parameters DataLoadStack:region="us-east-1" \
--parameters DataLoadStack:ingestRole="arn:aws:iam::YYYY:role/ingest-searchable-content" \
--parameters DataLoadStack:osHost="https://9v6e0jlve45rb3tj4o1f.us-east-1.aoss.amazonaws.com" \
--parameters DataLoadStack:osIndex="raw" \
--parameters DataLoadStack:externalId="ValorExternou8n4Fh4hFSauHbsm"

```
