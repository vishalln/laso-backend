"""Reusable Lambda construct — supports optional VPC, layers, security groups."""

from constructs import Construct
from aws_cdk import (
    Duration,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
)
from lib.config.backend_config import LAMBDA


class PythonLambdaConstruct(Construct):
    """Python Lambda function with optional VPC networking and layers."""

    function: _lambda.Function

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        path: str,
        handler: str,
        environment: dict[str, str] | None = None,
        vpc: ec2.IVpc | None = None,
        vpc_subnets: ec2.SubnetSelection | None = None,
        security_groups: list[ec2.SecurityGroup] | None = None,
        layers: list[_lambda.ILayerVersion] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.function = _lambda.Function(
            self, "Function",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler=handler,
            code=_lambda.Code.from_asset(path),
            timeout=Duration.seconds(LAMBDA.timeout_seconds),
            memory_size=LAMBDA.memory_mb,
            environment=environment or {},
            vpc=vpc,
            vpc_subnets=vpc_subnets,
            security_groups=security_groups,
            layers=layers or [],
            allow_public_subnet=True if vpc else None,
        )
