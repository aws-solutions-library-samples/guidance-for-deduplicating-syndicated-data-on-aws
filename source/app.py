#!/usr/bin/env python3
import os

from aws_cdk import Tags, App, Aspects
from cdk_nag import ( AwsSolutionsChecks ) #, NagSuppressions )
from search_content.config import OSS
from search_content.roles_stack import InitRolesStack
from search_content.dataload_stack import DataLoadStack
from search_content.search_content_stack import SearchContentStack
from search_content.lambdas_stack import LambdasStack

app = App()
init_roles = InitRolesStack(app, "RolesStack")

oss = SearchContentStack(app, "SearchContentStack", init_roles.roles['data_2_q_role'])
oss.add_dependency(init_roles)
Tags.of(oss).add("stack", "SearchContent");

lam = LambdasStack(app, "LambdasStack", oss.oss, [oss.layer], init_roles.roles)
Tags.of(lam).add("stack", "Lambdas");

load = DataLoadStack(app, "DataLoadStack", init_roles.roles['data_load_role']) ### to be deployed as cloudformation, not cdk
Tags.of(load).add("stack", "DataLoad");

Tags.of(app).add("app", "SearchContent");

Aspects.of(app).add(AwsSolutionsChecks())
app.synth()
