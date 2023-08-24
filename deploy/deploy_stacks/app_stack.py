from typing import Optional

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_rds as rds,
    aws_sqs as sqs,
    aws_iam as iam,
    aws_certificatemanager as certmgr,
    aws_s3 as s3,
    Stack,
    App,
    aws_ecs_patterns as patterns,
)
import pydantic

from .utils import generate_name


class DeploymentSettings(pydantic.BaseSettings):
    VPC_ID: str
    DOMAIN_NAME: str


class AppEnvSettings(pydantic.BaseSettings):
    DJANGO_ADMIN_URL: str = 'admg/'
    DJANGO_ALLOWED_HOSTS: str
    DJANGO_DEBUG: Optional[str] = "False"
    DB_NAME: str = "postgres"
    DJANGO_SECRET_KEY: str
    DJANGO_SECURE_SSL_REDIRECT: str
    # TODO make this more restrictive
    DJANGO_ALLOWED_HOSTS = "*"
    DJANGO_SECURE_SSL_REDIRECT = "True"
    CASEI_GH_TOKEN = "faketokenhere"

    GCMD_SYNC_SOURCE_EMAIL = "gcmd@uah.edu"
    GCMD_SYNC_RECIPIENTS = "random@test.mail"
    MIGRATE = "true"

    SENTRY_DSN = "https://c381d9c2a246497fa1d8dca4ade1cf98@o4504118897934336.ingest.sentry.io/4504118899179520"


class ApplicationStack(Stack):
    def __init__(
        self,
        app: App,
        stack_id: str,
        code_dir: str,
        queue: sqs.Queue,
        db: rds.DatabaseInstance,
        assets_bucket: s3.IBucket,
        stage: str,
        **kwargs,
    ) -> None:
        super().__init__(app, stack_id, **kwargs)

        # NOTE: We initialize this inside of the stack so that we don't require env variables
        # to be set when deploying other stacks.
        deployment_settings = DeploymentSettings(
            _env_file=(  # pyright: ignore NOTE: https://github.com/blakeNaccarato/pydantic/blob/c5a29ef77374d4fda85e8f5eb2016951d23dac33/docs/visual_studio_code.md?plain=1#L260-L272
                {"dev": ".env.staging", "prod": ".env.production"}.get(stage, "development")
            ),
        )
        app_env_settings = AppEnvSettings(
            _env_file=(  # pyright: ignore NOTE: https://github.com/blakeNaccarato/pydantic/blob/c5a29ef77374d4fda85e8f5eb2016951d23dac33/docs/visual_studio_code.md?plain=1#L260-L272
                {"dev": ".env.staging", "prod": ".env.production"}.get(stage, "development")
            ),
        )

        if not db.secret:
            raise Exception("DB does not have secret associated with it.")

        vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id=deployment_settings.VPC_ID)

        cluster = ecs.Cluster(
            self, 'cluster', vpc=vpc, cluster_name=generate_name('cluster', stage=stage)
        )

        image = ecs.ContainerImage.from_asset(code_dir, file="Dockerfile.prod")

        app_service = patterns.ApplicationLoadBalancedFargateService(
            self,
            {
                "dev": "admg-backend-fargate-service",
                "prod": "admg-production-fargate-service",
            }.get(stage, "development"),
            cluster=cluster,
            memory_limit_mib=1024,
            desired_count=1,
            cpu=512,
            task_image_options=patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image,
                environment={
                    **app_env_settings.dict(),
                    "AWS_S3_REGION_NAME": Stack.of(self).region,
                    "AWS_STORAGE_BUCKET_NAME": assets_bucket.bucket_name,
                    "DJANGO_SETTINGS_MODULE": "config.settings.production",
                    "SENTRY_ENV": {"dev": "staging", "prod": "production"}.get(
                        stage, "development"
                    ),
                    "CELERY_BROKER_URL": "sqs://",
                    "CELERY_TASK_DEFAULT_QUEUE": queue.queue_name,
                    "AWS_QUEUE_REGION_NAME": Stack.of(self).region,
                },
                secrets={
                    "DB_HOST": ecs.Secret.from_secrets_manager(db.secret, "host"),
                    "DB_USER": ecs.Secret.from_secrets_manager(db.secret, "username"),
                    "DB_PASSWORD": ecs.Secret.from_secrets_manager(db.secret, "password"),
                    "DB_PORT": ecs.Secret.from_secrets_manager(db.secret, "port"),
                },
            ),
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            load_balancer_name={
                "dev": 'admg-backend-loadbalancer',
                "prod": 'admg-production-loadbalancer',
            }.get(stage, "development"),
            certificate=certmgr.Certificate(
                self,
                id="cert",
                domain_name=deployment_settings.DOMAIN_NAME,
                certificate_name=f"admg {deployment_settings.DOMAIN_NAME} certificate",
                validation=certmgr.CertificateValidation.from_dns(),
            ),
        )

        app_service.target_group.configure_health_check(path="/accounts/login/")

        # Create a Fargate service that runs the Celery worker
        worker_service = patterns.QueueProcessingFargateService(
            self,
            'CeleryWorkerService',
            cluster=cluster,
            image=image,
            command=["celery", "-A", "config", "worker", "-l", "info"],
            queue=queue,
            environment={
                **app_env_settings.dict(),
                "AWS_S3_REGION_NAME": Stack.of(self).region,
                "AWS_STORAGE_BUCKET_NAME": assets_bucket.bucket_name,
                "DJANGO_SETTINGS_MODULE": "config.settings.production",
                "SENTRY_ENV": {"dev": "staging", "prod": "production"}.get(stage, "development"),
                "CELERY_BROKER_URL": "sqs://@",
                "AWS_QUEUE_REGION_NAME": Stack.of(self).region,
                "CELERY_TASK_DEFAULT_QUEUE": queue.queue_name,
            },
            secrets={
                "DB_HOST": ecs.Secret.from_secrets_manager(db.secret, "host"),
                "DB_USER": ecs.Secret.from_secrets_manager(db.secret, "username"),
                "DB_PASSWORD": ecs.Secret.from_secrets_manager(db.secret, "password"),
                "DB_PORT": ecs.Secret.from_secrets_manager(db.secret, "port"),
            },
            memory_limit_mib=512,
        )

        for service in [app_service, worker_service]:
            # Bucket Permissions
            assets_bucket.grant_read_write(service.task_definition.task_role)

            # DB Permissions
            service.service.connections.allow_to(db.connections, port_range=ec2.Port.tcp(5432))
            if service.task_definition.task_role:
                db.secret.grant_read(service.task_definition.task_role)

            # Queue Permissions
            queue.grant_send_messages(service.task_definition.task_role)
            service.task_definition.task_role.add_to_policy(  # type: ignore
                iam.PolicyStatement(
                    actions=[
                        "sqs:ListQueues",
                        "sqs:GetQueueAttributes",
                        "sqs:SendMessage",
                        "sqs:GetQueueUrl",
                    ],
                    resources=["*"],
                )
            )
