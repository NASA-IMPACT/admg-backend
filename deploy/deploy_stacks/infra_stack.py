from aws_cdk import (
    Stack,
    App,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_iam as iam,
)
import pydantic

from .utils import generate_name


class DeploymentSettings(pydantic.BaseSettings):
    vpc_id: str


class InfraStack(Stack):
    def __init__(self, app: App, stack_id: str, **kwargs) -> None:
        super().__init__(app, stack_id, **kwargs)

        iam.Role(
            self,
            "cicd-role",
            assumed_by=iam.WebIdentityPrincipal(
                "token.actions.githubusercontent.com",
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:NASA-IMPACT/admg-backend/:*"
                    }
                },
            ),
            role_name="admg-ci-role",
            inline_policies={
                "cdk_permissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["sts:AssumeRole"],
                            resources=["arn:aws:iam:::role/cdk-*"],
                        )
                    ]
                )
            },
        )

        # deployment_settings = DeploymentSettings(
        #     _env_file=(  # pyright: ignore NOTE: https://github.com/blakeNaccarato/pydantic/blob/c5a29ef77374d4fda85e8f5eb2016951d23dac33/docs/visual_studio_code.md?plain=1#L260-L272
        #         ".env"
        #     ),
        # )

        # vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id=deployment_settings.vpc_id)

        # self.bucket = s3.Bucket(
        #     self,
        #     "assets-bucket",
        #     bucket_name=generate_name("assets").replace("_", "-"),
        #     public_read_access=True,
        # )

        # self.db = rds.DatabaseInstance(
        #     self,
        #     "db",
        #     engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_13_4),
        #     instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
        #     vpc=vpc,
        #     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        # )
