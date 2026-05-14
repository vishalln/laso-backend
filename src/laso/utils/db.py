"""PostgreSQL connection -- reused across warm Lambda invocations."""

import json
import logging
import os

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

from laso.utils.retry import with_retry

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


@with_retry()
def execute(query: str, params: tuple = None) -> list[dict]:
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if cur.description:
            return [dict(row) for row in cur.fetchall()]
        return []


@with_retry()
def execute_one(query: str, params: tuple = None) -> dict | None:
    rows = execute(query, params)
    return rows[0] if rows else None


@with_retry()
def insert(query: str, params: tuple = None) -> None:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)


def update_by_id(table: str, id_col: str, id_val, **fields) -> None:
    """Update specific columns by ID."""
    if not fields:
        return
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    query = f"UPDATE {table} SET {set_clause} WHERE {id_col} = %s"
    params = tuple(fields.values()) + (id_val,)
    log.info("update_by_id | table=%s id=%s fields=%s", table, id_val, list(fields.keys()))
    execute(query, params)


def delete_by_id(table: str, id_col: str, id_val) -> None:
    """Delete row by ID."""
    query = f"DELETE FROM {table} WHERE {id_col} = %s"
    log.info("delete_by_id | table=%s id=%s", table, id_val)
    execute(query, (id_val,))
