"""CDK-level data infrastructure configuration — VPC, RDS (free tier), Lambda Layer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VpcConfig:
    """VPC networking — 0 NAT gateways to stay free tier."""
    name: str = "laso-vpc"
    max_azs: int = 2
    nat_gateways: int = 0
    public_cidr_mask: int = 24
    isolated_cidr_mask: int = 24
    lambda_sg_name: str = "laso-lambda-sg"


@dataclass(frozen=True)
class RdsConfig:
    """Free tier: db.t3.micro, 20GB gp2, PostgreSQL 15, single-AZ."""
    instance_id: str = "laso-db"
    database_name: str = "laso"
    port: int = 5432
    allocated_storage_gb: int = 20
    max_allocated_storage_gb: int = 20
    backup_retention_days: int = 1
    multi_az: bool = False
    publicly_accessible: bool = True
    deletion_protection: bool = False
    rds_sg_name: str = "laso-rds-sg"


@dataclass(frozen=True)
class SecretConfig:
    secret_name: str = "laso/rds/credentials"
    username: str = "laso_admin"
    password_length: int = 30


@dataclass(frozen=True)
class LayerConfig:
    name: str = "laso-psycopg2"
    asset_path: str = "layers/dependencies"
    description: str = "psycopg2-binary for PostgreSQL Lambda access"


VPC = VpcConfig()
RDS = RdsConfig()
SECRET = SecretConfig()
LAYER = LayerConfig()
