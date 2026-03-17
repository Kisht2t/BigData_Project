"""Boto3 client factories with LocalStack support for local development."""

from __future__ import annotations

import os

import boto3
from botocore.config import Config

_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
_AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
_LOCALSTACK_ENDPOINT = "http://localstack:4566"

_boto_kwargs: dict = {
    "region_name": _AWS_REGION,
}

if _ENVIRONMENT == "local":
    _boto_kwargs["endpoint_url"] = _LOCALSTACK_ENDPOINT
    _boto_kwargs["aws_access_key_id"] = "test"
    _boto_kwargs["aws_secret_access_key"] = "test"


def get_sqs_client():
    return boto3.client("sqs", **_boto_kwargs)


def get_dynamodb_resource():
    return boto3.resource("dynamodb", **_boto_kwargs)


def get_s3_client():
    return boto3.client(
        "s3",
        **_boto_kwargs,
        config=Config(signature_version="s3v4"),
    )


def get_secrets_client():
    """Only used in production — returns real Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=_AWS_REGION)
