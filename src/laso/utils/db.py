"""PostgreSQL connection -- reused across warm Lambda invocations."""

import json
import logging
import os

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)

_connection = None


def get_connection():
    global _connection
    if _connection and not _connection.closed:
        return _connection

    secret_arn = os.environ["DB_SECRET_ARN"]
    client = boto3.client("secretsmanager")
    secret = json.loads(client.get_secret_value(SecretId=secret_arn)["SecretString"])

    _connection = psycopg2.connect(
        host=secret["host"],
        port=secret["port"],
        dbname=secret["dbname"],
        user=secret["username"],
        password=secret["password"],
        connect_timeout=5,
    )
    _connection.autocommit = True
    return _connection


def execute(query: str, params: tuple = None) -> list[dict]:
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if cur.description:
            return [dict(row) for row in cur.fetchall()]
        return []


def execute_one(query: str, params: tuple = None) -> dict | None:
    rows = execute(query, params)
    return rows[0] if rows else None


def insert(query: str, params: tuple = None) -> None:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
