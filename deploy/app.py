import os

import aws_cdk as core

from deploy_stacks.utils import generate_name

from deploy_stacks.app_stack import ApplicationStack
from deploy_stacks.infra_stack import InfraStack


CDK_DEFAULT_REGION = os.environ.get("CDK_DEFAULT_REGION")
CDK_DEFAULT_ACCOUNT = os.environ.get("CDK_DEFAULT_ACCOUNT")

env = core.Environment(region=CDK_DEFAULT_REGION, account=CDK_DEFAULT_ACCOUNT)

app = core.App()

infra_stack = InfraStack(app, generate_name("infra"), env=env)

ApplicationStack(
    app,
    generate_name("application"),
    code_dir="./app",
    # url_prefix='data-in-action',
    # db=infra_stack.db,
    # assets_bucket=infra_stack.bucket,
    env=env,
)

app.synth()
