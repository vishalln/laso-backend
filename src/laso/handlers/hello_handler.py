"""Hello handler — simple greeting endpoint."""

import json
import logging

log = logging.getLogger(__name__)


def say_hello(name: str = "World") -> dict:
    """Business logic for saying hello."""
    return {"message": f"Hello, {name}!"}


def lambda_handler(event: dict, context) -> dict:
    """Lambda entry point for API Gateway."""
    log.info("hello_handler | event=%s", event)
    
    # Parse request body if present
    body = {}
    if event.get("body"):
        body = json.loads(event["body"])
    
    name = body.get("name", "World")
    result = say_hello(name)
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result)
    }
