# Guidance for Mastering Syndicated Data on AWS

## Table of Content

List the top-level sections of the README template, along with a hyperlink to the specific section.

### Required

1. [Overview](#overview-required)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites)
    - [Operating System](#operating-system)
3. [Deployment](#deployment)
4. [Deployment Validation](#deployment-validation-required)
5. [Running the Guidance](#running-the-guidance-required)
6. [Next Steps](#next-steps-required)
7. [Cleanup](#cleanup-required)

***Optional***

8. [FAQ, known issues, additional considerations, and limitations](#faq-known-issues-additional-considerations-and-limitations-optional)
9. [Revisions](#revisions-optional)
10. [Notices](#notices-optional)
11. [Authors](#authors-optional)

## Overview (required)

1. Provide a brief overview explaining the what, why, or how of your Guidance. You can answer any one of the following to help you write this:

    - **Why did you build this Guidance?**
    - **What problem does this Guidance solve?**

2. Include the architecture diagram image, as well as the steps explaining the high-level overview and flow of the architecture.
    - To add a screenshot, create an ‘assets/images’ folder in your repository and upload your screenshot to it. Then, using the relative file path, add it to your README.

### Cost ( required )

[budget](https://calculator.aws/#/estimate?id=214ad9dd9ff23aa8726ec2986f2f1de5c4873b10)

This section is for a high-level cost estimate. Think of a likely straightforward scenario with reasonable assumptions based on the problem the Guidance is trying to solve. Provide an in-depth cost breakdown table in this section below ( you should use AWS Pricing Calculator to generate cost breakdown ).

Start this section with the following boilerplate text:

_You are responsible for the cost of the AWS services used while running this Guidance. As of <month> <year>, the cost for running this Guidance with the default settings in the <Default AWS Region (Most likely will be US East (N. Virginia)) > is approximately $<n.nn> per month for processing ( <nnnnn> records )._

Replace this amount with the approximate cost for running your Guidance in the default Region. This estimate should be per month and for processing/serving resonable number of requests/entities.

Suggest you keep this boilerplate text:
_We recommend creating a [Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) through [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) to help manage costs. Prices are subject to change. For full details, refer to the pricing webpage for each AWS service used in this Guidance._

### Sample Cost Table ( required )

**Note : Once you have created a sample cost table using AWS Pricing Calculator, copy the cost breakdown to below table and upload a PDF of the cost estimation on BuilderSpace.**

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.

| AWS service  | Dimensions | Cost [USD] |
| ----------- | ------------ | ------------ |
| Amazon API Gateway | 1,000,000 REST API calls per month  | $ 3.50month |
| Amazon Cognito | 1,000 active users per month without advanced security feature | $ 0.00 |

## Prerequisites

### Operating System

- This guide can be operated on any personal or server Operating System (OS) such as *Mac, Linux, or Windows* that include a **terminal** as well as on Cloud Environments. i.e., AWS EC2, AWS Cloud9.


### Third-party tools

1. A Terminal Interface
2. AWS CLI. [install instructions here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. Node.js 14.15.0 or later [install instructions here](https://nodejs.org/en/download/)
4. AWS CDK CLI [getting started guide](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)
5. Python 3.11 (virtual environment preferred)

### Python virtual environment creation
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

### AWS account requirements

This deployment requires you have permissions to deploy CloudFormation templates in your AWS account

**Deeployable resources:**
- CloudFormation Stacks
- SQS
- OpenSearch Serverless Collections
- IAM roles and policies
- Lambdas


### aws cdk bootstrap

This Guidance uses aws-cdk. If you are using aws-cdk for first time, please follow [**cdk getting started guide**](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) first and perform the below bootstrapping in every AWS Account you will deploy.

Make sure you have AWS credentials available in your terminal and run:

```shell
cdk bootstrap
```

### Supported Regions

 OpenSearch Serverless is now available in eight AWS Regions globally: US East (Ohio), US East (N. Virginia), US West (Oregon), Asia Pacific (Singapore), Asia Pacific (Sydney), Asia Pacific (Tokyo), Europe (Frankfurt), and Europe (Ireland).

 Check updates here: https://aws.amazon.com/about-aws/whats-new/2023/01/amazon-opensearch-serverless-available

## Deployment

### Deploy Prerequisites

1. Install [3rd Party tools](#third-party-tools)
2. Clone the repo using command:
```shell
git clone https://github.com/aws-solutions-library-samples/guidance-for-mastering-syndicated-data-on-aws.git
```
3. cd to the *source* folder in repo ```cd guidance-for-mastering-syndicated-data-on-aws/source```
4. Make sure you have a python environment active. See [here](#python-virtual-environment-creation) how.

5. Install packages in requirements using commands
```shell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```


### Deploy Step 00 - cdk bootstrap - *Main* & *Secondary* accounts

Set AWS credentials for the **Account** where the infrastructure will be deployed and run **cdk bootstrap**

```shell
cdk bootstrap
```

### Deploy Step 01 - RolesStack Deployment - *Main* & *Secondary* accounts

This stack contains lambda roles that will be neccesary in other stacks. Without this other stacks will fail to deploy or not work correctly.

```shell
cdk deploy RolesStack
```

### Deploy Step 02 - SearchContentStack Deployment - *Main* account only

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
--parameters SearchContentStack:ADPRINCIPALS="<admin roles - n>"

```shell
cdk deploy SearchContentStack \
--parameters SearchContentStack:EXPRINCIPALS="arn:aws:sts::XXXX:assumed-role/DataLoadStack-ExternalIngestionRole/OpenSearchDataload,arn:aws:sts::YYYY:assumed-role/DataLoadStack-ExternalIngestionRole/OpenSearchDataload" \
--parameters SearchContentStack:ADPRINCIPALS="arn:aws:sts::YYYY:assumed-role/Admin/<user>,arn:aws:sts::YYYY:assumed-role/AmazonSageMakerServiceCatalogProductsUseRole/SageMaker"

```


### Deploy Step 03 - LambdasStack Deployment - *Main* account only

* searchIndex: is the name of the search index deployed in *SearchContentStack*. Default: `raw`

* vectorIndex: is the name of the vector index deployed in *SearchContentStack*. Default: `fultable_dedup`

See `search_content/config.py` for other default details.

```shell
cdk deploy LambdasStack \
--parameters LambdasStack:searchIndex=raw \
--parameters LambdasStack:vectorIndex=fultable_dedup

```

### Deploy Step 04 - DataLoadStack Deployment - *Main* & *Secondary* accounts

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

## Deployment Validation  (required)

<Provide steps to validate a successful deployment, such as terminal output, verifying that the resource is created, status of the CloudFormation template, etc.>


**Examples:**

* Open CloudFormation console and verify the status of the template with the name starting with xxxxxx.
* If deployment is successful, you should see an active database instance with the name starting with <xxxxx> in        the RDS console.
*  Run the following CLI command to validate the deployment: ```aws cloudformation describe xxxxxxxxxxxxx```



## Running the Guidance (required)

<Provide instructions to run the Guidance with the sample data or input provided, and interpret the output received.>

This section should include:

* Guidance inputs
* Commands to run
* Expected output (provide screenshot if possible)
* Output description



## Next Steps (required)

Provide suggestions and recommendations about how customers can modify the parameters and the components of the Guidance to further enhance it according to their requirements.


## Cleanup (required)

- Include detailed instructions, commands, and console actions to delete the deployed Guidance.
- If the Guidance requires manual deletion of resources, such as the content of an S3 bucket, please specify.



## FAQ, known issues, additional considerations, and limitations (optional)


**Known issues (optional)**

<If there are common known issues, or errors that can occur during the Guidance deployment, describe the issue and resolution steps here>


**Additional considerations (if applicable)**

<Include considerations the customer must know while using the Guidance, such as anti-patterns, or billing considerations.>

**Examples:**

- “This Guidance creates a public AWS bucket required for the use-case.”
- “This Guidance created an Amazon SageMaker notebook that is billed per hour irrespective of usage.”
- “This Guidance creates unauthenticated public API endpoints.”


Provide a link to the *GitHub issues page* for users to provide feedback.


**Example:** *“For any feedback, questions, or suggestions, please use the issues tab under this repo.”*

## Revisions (optional)

Document all notable changes to this project.

Consider formatting this section based on Keep a Changelog, and adhering to Semantic Versioning.

## Notices (optional)

Include a legal disclaimer

**Example:**
*Customers are responsible for making their own independent assessment of the information in this Guidance. This Guidance: (a) is for informational purposes only, (b) represents AWS current product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. AWS responsibilities and liabilities to its customers are controlled by AWS agreements, and this Guidance is not part of, nor does it modify, any agreement between AWS and its customers.*


## Authors (optional)

Name of code contributors
