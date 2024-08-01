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


class OSCollection(Construct):

    def __init__(self, scope: "Construct", contruct_id: str,
        parameters: Dict[str, List[str]],
        collection_cfg: OSS_COLLECTION,
        addAdditionalPrincipals: bool = False) -> None:
        super().__init__(scope, contruct_id)

        self.add_additional_principals = addAdditionalPrincipals
        self.additional_admin_vector_principals = parameters['additional_admin_vector_principals']
        self.external_principals = parameters['EXTERNAL_PRINCIPALS']
        self.admin_principals = parameters['ADMIN_PRINCIPALS']
        self.admin_init_roles = parameters['admin_init_role_arns']
        self.collection_cfg = collection_cfg
        self.region = Stack.of(self).region
        self.account = Stack.of(self).account

        secPolicy = self.createSecurityPolicy()
        netPolicy = self.createNetworkPolicy()

        self.collection = self.createCollection(coll=collection_cfg)
        self.collection.add_dependency(netPolicy)
        self.collection.add_dependency(secPolicy)

        accAdminPolicy = self.createAdminAccessPolicy()
        accAdminPolicy.add_dependency(self.collection)

        if collection_cfg.isRemoteEnabled:
            accRemotePolicy = self.createRemoteAccessPolicy()
            accRemotePolicy.add_dependency(accAdminPolicy)


    def createCollection(self, coll:OSS_COLLECTION)-> CfnCollection:
        return CfnCollection(self, "ContentCollection",
            name=coll.name,

            # the properties below are optional
            # description="description",
            # standby_replicas="standbyReplicas",
            type=coll.type
        )

    def createAdminAccessPolicy(self)-> CfnAccessPolicy:
        ## Access Policy must be created after Lambda Role that will be used to
        ## consume data

        adminRole = self.createAdminRoles(self.admin_principals, "Normal")
        adminRoleInit = self.createAdminRoles(self.admin_init_roles, "Init")
        adminRoles = [adminRoleInit, adminRole]
        self.admin_role_init = adminRoleInit
        rules = [
            {
                "Rules": [
                    {
                        "Resource": [f"collection/{self.collection_cfg.name}"],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems"
                        ],
                        "ResourceType": "collection"
                    },
                    {
                        "Resource": [f"index/{self.collection_cfg.name}/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument"
                        ],
                        "ResourceType": "index"
                    }
                ],
                "Principal": adminRoles,
                "Description": "Admin data policy"
            }
        ]

        return CfnAccessPolicy(self, "AdminAccessPolicy",
            name=f"{self.collection_cfg.type.lower()}-admin-access-policy",
            policy=json.dumps(rules),
            type="data"
        )

    def createRemoteAccessPolicy(self)-> CfnAccessPolicy:
         ## Access Policy must be created after Lambda Role that will be used to
         ## consume data

         rules = [
             {
                 "Rules": [
                     {
                         "Resource": [f"collection/{self.collection_cfg.name}"],
                         "Permission": [
                             "aoss:DescribeCollectionItems"
                         ],
                         "ResourceType": "collection"
                     },
                     {
                         "Resource": [f"index/{self.collection_cfg.name}/*"],
                         "Permission": [
                             "aoss:DescribeIndex",
                             "aoss:ReadDocument",
                             "aoss:WriteDocument"
                         ],
                         "ResourceType": "index"
                     }
                 ],
                 "Principal": self.createRemoteRoles(),
                 "Description": "Ingestion data policy"
             }
         ]

         return CfnAccessPolicy(self, "IngestAccessPolicy",
             name=f"{self.collection_cfg.type.lower()}-ingest-access-policy",
             policy=json.dumps(rules),
             type="data"
         )

    def createSecurityPolicy(self)-> CfnSecurityPolicy:
        policy = {
            "Rules": [
                {
                    "Resource": [f"collection/{self.collection_cfg.name}"],
                    "ResourceType": "collection"
                }
            ],
            "AWSOwnedKey": True
        }
        return CfnSecurityPolicy(self, "SecurityPolicy",
         name=f"{self.collection_cfg.type.lower()}-security-policy",
         policy=json.dumps(policy),
         type="encryption"
        )

    def createNetworkPolicy(self, vpcIdList: List[str] = [])->CfnSecurityPolicy:
        policy= {
            "Rules": [
                {
                    "Resource": [f"collection/{self.collection_cfg.name}"],
                    "ResourceType": "collection"
                },
                {
                    "ResourceType":"dashboard",
                    "Resource": [f"collection/{self.collection_cfg.name}"]
                }
            ],
            "AllowFromPublic": True,
            # "SourceVPCEs": vpcIdList
        }

        policies = [policy]

        return CfnSecurityPolicy(self, "NetworkPolicy",
            name=f"{self.collection_cfg.type.lower()}-network-policy",
            policy=json.dumps(policies),
            type="network"
        )


    def createRemoteRoles(self)->List[str]:

        principal_list = [
                _iam.ArnPrincipal(principal_arn)
                for principal_arn in self.external_principals
        ]

        union_principals = _iam.CompositePrincipal(*principal_list) #type: ignore

        principalWithConditions = _iam.PrincipalWithConditions(
            principal=union_principals, #type: ignore
            conditions={
                "StringEquals": {
                    "sts:ExternalId": OSS.REMOTE_EXTERNAL_ID
                }
            }
        )

        ingestionRole = _iam.Role(
            self, 'IngestionRole',
            role_name=OSS.REMOTE_ACCESS_ROLE_NAME,
            assumed_by=principalWithConditions,
        )

        ingestionRole.attach_inline_policy(
            _iam.Policy(
                self, 'IngestionPolicy',
                statements=[
                    _iam.PolicyStatement(
                        actions=[
                            'aoss:APIAccessAll'
                        ],
                        resources=[
                            f'arn:aws:aoss:{self.region}:{self.account}:collection/{self.collection.attr_id}',
                        ]
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'aoss:ListCollections'
                        ],
                        resources=['*']
                    )
                ]
            )
        )

        ## Using one role for now
        return [
            ingestionRole.role_arn,
            f"arn:aws:sts::{self.account}:assumed-role/{LambdaDelta2QueueCfg.INGESTION_ROLE_NAME}/{LambdaDelta2QueueCfg.NAME}"
        ]

    def createAdminRoles(self, principal_arns: List[str], suffix: str)->str:

        principal_list = [
                _iam.ArnPrincipal(principal_arn)
                for principal_arn in principal_arns
        ]

        union_principals = _iam.CompositePrincipal(*principal_list) #type: ignore

        if self.add_additional_principals:
            additional_principal_list = [
                    _iam.ArnPrincipal(principal_arn)
                    for principal_arn in [f'arn:aws:sts::{self.account}:assumed-role/{LambdaDelta2QueueCfg.INGESTION_ROLE_NAME}/{LambdaDelta2QueueCfg.NAME}']
                    #self.additional_admin_vector_principals
            ]
            # additional_union_principals = _iam.CompositePrincipal(*additional_principal_list) #type: ignore
            # all_union_principals = _iam.CompositePrincipal(additional_union_principals, union_principals) #type: ignore
            # all_union_principals = union_principals
            for prin in additional_principal_list:
                # union_principals.add_principals(prin) # type: ignore
                pass

        principalWithConditions = _iam.PrincipalWithConditions(
            principal=union_principals, #type: ignore
            conditions={
                "StringEquals": {
                    "sts:ExternalId": OSS.ADMIN_EXTERNAL_ID
                }
            }
        )

        adminRole = _iam.Role(
            self, f'AdminRole{suffix}',
            role_name=self.collection_cfg.type.lower()+OSS.ADMIN_ACCESS_ROLE_NAME+suffix,
            assumed_by=principalWithConditions,
        )

        adminRole.attach_inline_policy(
            _iam.Policy(
                self, f'AdminPolicy{suffix}',
                statements=[
                    _iam.PolicyStatement(
                        actions=[
                            'aoss:APIAccessAll',
                            'aoss:UpdateCollection',
                            'aoss:UpdateAccountSettings'
                        ],
                        resources=[
                            f'arn:aws:aoss:{self.region}:{self.account}:collection/{self.collection.attr_id}',
                        ]
                    ),
                    _iam.PolicyStatement(
                        actions=[
                            'aoss:ListCollections'
                        ],
                        resources=['*']
                    )
                ]
            )
        )

        ## Using one role for now
        return adminRole.role_arn
