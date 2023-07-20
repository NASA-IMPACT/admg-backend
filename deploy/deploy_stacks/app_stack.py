from typing import Optional

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_rds as rds,
    aws_s3 as s3,
    aws_elasticloadbalancingv2 as elbv2,
    Stack,
    App,
    Duration,
    aws_ecs_patterns as patterns,
)
import pydantic

from .utils import generate_name


class DeploymentSettings(pydantic.BaseSettings):
    vpc_id: str


class AppEnvSettings(pydantic.BaseSettings):
    DJANGO_ADMIN_URL: str = '/admin'
    DJANGO_ALLOWED_HOSTS: str
    DJANGO_DEBUG: Optional[str] = "False"
    DJANGO_SECRET_KEY: str
    DJANGO_SECURE_SSL_REDIRECT: str
    DJANGO_SETTINGS_MODULE: Optional[str] = "server.settings.main"
    DJANGO_SUPERUSER_EMAIL: str
    DJANGO_SUPERUSER_PASSWORD: str
    DJANGO_SUPERUSER_USERNAME: str
    MAILGUN_API_KEY: Optional[str] = ""
    MAILGUN_DOMAIN: Optional[str] = ""

    DB_NAME: str = 'postgres'


class ApplicationStack(Stack):
    def __init__(
        self,
        app: App,
        stack_id: str,
        code_dir: str,
        db: rds.DatabaseInstance,
        assets_bucket: s3.IBucket,
        # url_prefix: str,
        **kwargs,
    ) -> None:
        super().__init__(app, stack_id, **kwargs)

        # NOTE: We initialize this inside of the stack so that we don't require env variables
        # to be set when deploying other stacks.
        deployment_settings = DeploymentSettings(
            _env_file=(  # pyright: ignore NOTE: https://github.com/blakeNaccarato/pydantic/blob/c5a29ef77374d4fda85e8f5eb2016951d23dac33/docs/visual_studio_code.md?plain=1#L260-L272
                ".env"
            ),
        )
        app_env_settings = AppEnvSettings(
            _env_file=(  # pyright: ignore NOTE: https://github.com/blakeNaccarato/pydantic/blob/c5a29ef77374d4fda85e8f5eb2016951d23dac33/docs/visual_studio_code.md?plain=1#L260-L272
                ".env"
            ),
        )

        # if not db.secret:
        #     raise Exception("DB does not have secret associated with it.")

        vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id=deployment_settings.vpc_id)

        cluster = ecs.Cluster(self, 'cluster', vpc=vpc, cluster_name=generate_name('cluster'))
        patterns.ApplicationLoadBalancedFargateService(
            self,
            "admg-backend-fargate-service",
            cluster=cluster,
            memory_limit_mib=1024,
            desired_count=1,
            cpu=512,
            task_image_options=patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
            ),
            # task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            task_subnets=ec2.SubnetSelection(
                subnets=[ec2.Subnet.from_subnet_id(self, "subnet", "subnet-0d9b54d7f70ac8940")]
            ),
            load_balancer_name='admg-backend-loadbalancer',
        )

        # image = ecs.ContainerImage.from_asset(code_dir, target='prod')
        # task_definition = ecs.FargateTaskDefinition(
        #     self,
        #     "api-definition",
        # )
        # task_definition.add_container(
        #     "container",
        #     image=image,
        #     environment={
        #         **app_env_settings.dict(),
        #         "URL_PREFIX": url_prefix,
        #         "AWS_REGION": Stack.of(self).region,
        #         "AWS_S3_BUCKET": assets_bucket.bucket_name,
        #     },
        #     secrets={
        #         "DB_HOST": ecs.Secret.from_secrets_manager(db.secret, "host"),
        #         "DB_USER": ecs.Secret.from_secrets_manager(db.secret, "username"),
        #         "DB_PASSWORD": ecs.Secret.from_secrets_manager(db.secret, "password"),
        #         "DB_PORT": ecs.Secret.from_secrets_manager(db.secret, "port"),
        #     },
        #     logging=ecs.AwsLogDriver(stream_prefix="container"),
        #     # memory_limit_mib=528,
        #     # memory_reservation_mib=256,
        #     stop_timeout=Duration.seconds(2),
        # ).add_port_mappings(ecs.PortMapping(container_port=80))

        # service = ecs.FargateService(
        #     self,
        #     "Api",
        #     service_name=generate_name('service'),
        #     task_definition=task_definition,
        #     cluster=cluster,
        # )

        # # Bucket Permissions
        # assets_bucket.grant_read_write(task_definition.task_role)

        # # DB Permissions
        # service.connections.allow_to(db.connections, port_range=ec2.Port.tcp(5432))

        # db.secret.grant_read(task_definition.task_role)
        # if task_definition.execution_role:
        #     db.secret.grant_read(task_definition.execution_role)

        # # Load Balancer Config
        # listener = elbv2.ApplicationListener.from_lookup(
        #     self, 'listener', listener_arn=deployment_settings.alb_listener_arn
        # )

        # target_group = elbv2.ApplicationTargetGroup(
        #     self,
        #     'target-group',
        #     target_group_name=generate_name('target'),
        #     protocol=elbv2.ApplicationProtocol.HTTP,
        #     vpc=vpc,
        #     targets=[service],
        # )

        # target_group.configure_health_check(
        #     path=f"/{url_prefix}/ping",
        #     healthy_http_codes='200',
        # )

        # listener.add_target_groups(
        #     'target',
        #     target_groups=[target_group],
        #     conditions=[elbv2.ListenerCondition.path_patterns([f'/{url_prefix}*'])],
        #     priority=201,
        # )

        # # TODO: Add service to Cloudfront Distribution at `url_prefix`
        # # See: https://repost.aws/questions/QUiwOVmbCNR2iM666bi0WOfw/how-to-add-domain-alias-to-existing-cloud-front-distribution-using-cdk
