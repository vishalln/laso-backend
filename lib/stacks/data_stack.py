"""Data Stack — RDS PostgreSQL (free tier), Secrets Manager."""

from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Duration,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
)
from lib.config.data_config import RDS, SECRET


class DataStack(Stack):
    """RDS instance and credentials — receives VPC from VpcStack."""

    db_secret: secretsmanager.Secret
    db_instance: rds.DatabaseInstance

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        lambda_sg: ec2.SecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        rds_sg = self._create_rds_sg(vpc, lambda_sg)
        self.db_secret = self._create_db_secret()
        self.db_instance = self._create_rds_instance(vpc, rds_sg)
        self._create_outputs()

    def _create_rds_sg(self, vpc: ec2.IVpc, lambda_sg: ec2.SecurityGroup) -> ec2.SecurityGroup:
        sg = ec2.SecurityGroup(
            self, "RdsSg",
            vpc=vpc,
            security_group_name=RDS.rds_sg_name,
            description="RDS ingress from Lambda SG only",
            allow_all_outbound=False,
        )
        sg.add_ingress_rule(
            peer=lambda_sg,
            connection=ec2.Port.tcp(RDS.port),
            description="PostgreSQL from Lambda",
        )
        return sg

    def _create_db_secret(self) -> secretsmanager.Secret:
        return secretsmanager.Secret(
            self, "DbSecret",
            secret_name=SECRET.secret_name,
            description="LASO RDS PostgreSQL credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=f'{{"username": "{SECRET.username}"}}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=SECRET.password_length,
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )

    def _create_rds_instance(self, vpc: ec2.IVpc, rds_sg: ec2.SecurityGroup) -> rds.DatabaseInstance:
        return rds.DatabaseInstance(
            self, "LasoDb",
            instance_identifier=RDS.instance_id,
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[rds_sg],
            credentials=rds.Credentials.from_secret(self.db_secret),
            database_name=RDS.database_name,
            allocated_storage=RDS.allocated_storage_gb,
            max_allocated_storage=RDS.max_allocated_storage_gb,
            storage_type=rds.StorageType.GP2,
            multi_az=RDS.multi_az,
            publicly_accessible=RDS.publicly_accessible,
            backup_retention=Duration.days(RDS.backup_retention_days),
            deletion_protection=RDS.deletion_protection,
            removal_policy=RemovalPolicy.RETAIN,
        )

    def _create_outputs(self) -> None:
        CfnOutput(self, "DbHost",
                  value=self.db_instance.db_instance_endpoint_address,
                  export_name="LasoDbHost")
        CfnOutput(self, "DbSecretArn",
                  value=self.db_secret.secret_arn,
                  export_name="LasoDbSecretArn")
