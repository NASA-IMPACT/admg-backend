from aws_cdk import (
    Stack,
    App,
    Duration,
    aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_iam as iam,
)
import pydantic

from .utils import generate_name


class DeploymentSettings(pydantic.BaseSettings):
    VPC_ID: str


class InfraStack(Stack):
    def __init__(self, app: App, stack_id: str, stage: str, **kwargs) -> None:
        super().__init__(app, stack_id, **kwargs)

        iam.Role(
            self,
            "cicd-role",
            assumed_by=iam.WebIdentityPrincipal(
                "token.actions.githubusercontent.com",
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:NASA-IMPACT/admg-backend:*"
                    }
                },
            ),
            role_name={f"admg-ci-{stage}-role"},
            inline_policies={
                "cdk_permissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["sts:AssumeRole"],
                            resources=[f"arn:aws:iam::{Stack.of(self).account}:role/cdk-*"],
                        )
                    ]
                ),
                "admg_infra_policy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:PutObject"],
                            resources=[f"arn:aws:s3:::admg-{stage}-assets/*"],
                        )
                    ]
                ),
            },
        )

        deployment_settings = DeploymentSettings(
            _env_file=(  # pyright: ignore NOTE: https://github.com/blakeNaccarato/pydantic/blob/c5a29ef77374d4fda85e8f5eb2016951d23dac33/docs/visual_studio_code.md?plain=1#L260-L272
                # TODO get from env variable
                {"dev": ".env.staging", "prod": ".env.production"}.get(stage, "development")
            ),
        )

        vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id=deployment_settings.VPC_ID)

        self.bucket: s3.Bucket = s3.Bucket(
            self,
            "assets-bucket",
            # TODO pull from env
            bucket_name=generate_name("assets", stage=stage).replace("_", "-"),
            access_control=s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
        )

        self.queue = sqs.Queue(self, "MessageBroker", visibility_timeout=Duration.minutes(10))

        self.db = rds.DatabaseInstance(
            self,
            "db",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_14_8),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )
