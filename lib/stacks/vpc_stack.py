"""VPC Stack — shared networking for all LASO stacks."""

from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
)
from lib.config.data_config import VPC


class VpcStack(Stack):
    """Standalone VPC stack — passed to RDS, Lambda, and any future stacks."""

    vpc: ec2.Vpc
    lambda_sg: ec2.SecurityGroup

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self, "LasoVpc",
            vpc_name=VPC.name,
            max_azs=VPC.max_azs,
            nat_gateways=VPC.nat_gateways,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=VPC.public_cidr_mask,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=VPC.isolated_cidr_mask,
                ),
            ],
        )

        self.lambda_sg = ec2.SecurityGroup(
            self, "LambdaSg",
            vpc=self.vpc,
            security_group_name=VPC.lambda_sg_name,
            description="Security group for LASO Lambda functions",
            allow_all_outbound=True,
        )

        # VPC endpoints so Lambda in public subnet can reach AWS services without NAT
        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[self.lambda_sg],
        )

        CfnOutput(self, "VpcId", value=self.vpc.vpc_id, export_name="LasoVpcId")
