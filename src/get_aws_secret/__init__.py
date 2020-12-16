import base64
from dataclasses import dataclass
import os
from typing import Optional

import boto3
import botocore

from get_aws_secret import constants as c


@dataclass
class AwsSecret():
    memo: Optional[bool] = None
    client: Optional[botocore.client.BaseClient] = None
    version_id: Optional[str] = c.DEFAULT_SECRET_VERSION_ID
    version_stage: Optional[str] = c.DEFAULT_SECRET_VERSION_STAGE
    base64_decode: Optional[bool] = c.DEFAULT_BASE64_ENCODE_ARG
    bytes_decode: Optional[bool] = c.DEFAULT_BYTES_ENCODE_ARG
    encoding: Optional[str] = c.DEFAULT_ENCODING

    def get(self, secret_identifier: str) -> str:
        return get_secret(
            secret_identifier=secret_identifier,
            memo=self.memo,
            client=self.client,
            version_id=self.version_id,
            version_stage=self.version_stage,
            base64_decode=self.base64_decode,
            bytes_decode=self.bytes_decode,
            encoding=self.encoding,
        )


def new_boto3_client():
    return boto3.client('secretsmanager')


def get_client(default):
    '''Check boto3 default client, create a new one if not valid'''
    if isinstance(default, botocore.client.BaseClient):
        return default

    return new_boto3_client()


def extract_secret_from_boto3_response(
        response: dict,
        base64_decode: bool = True,
        bytes_decode: bool = True,
        encoding: str = c.DEFAULT_ENCODING,
        ) -> str:
    '''Extract a string or binary secret value from a boto3 response

    Detects when secret value is in binary format and automatically decode it
    from base64 bytes to a plain string before returning.

    Optionally pass 'base64_decode' (bool), 'bytes_decode' (bool), 'encoding'
    (str) arguments to control if and how a binary secret is decoded.
    '''
    if 'SecretString' in response.keys():
        return response['SecretString']
    else:
        secret_val = response['SecretBinary']

        if base64_decode:
            secret_val = base64.b64decode(secret_val)

        if bytes_decode:
            secret_val = secret_val.decode(encoding)

        return secret_val


def get_secret(
        # Secret Key or ARN (will be passed to boto3 client.get_secret_value)
        secret_identifier: str,

        # Environment var memoization
        memoize: Optional[bool] = None,

        # Args for the client.get_secret_value method
        client: Optional[botocore.client.BaseClient] = None,
        version_id: Optional[str] = c.DEFAULT_SECRET_VERSION_ID,
        version_stage: Optional[str] = c.DEFAULT_SECRET_VERSION_STAGE,

        # Secret decoding args (used in extract_secret_from_boto3_response)
        base64_decode: Optional[bool] = True,
        bytes_decode: Optional[bool] = True,
        encoding: Optional[str] = c.DEFAULT_ENCODING,
        ) -> str:
    if memoize is True and secret_identifier in os.environ.keys():
        return os.environ[secret_identifier]

    client = get_client(client)

    response = client.get_secret_value(
        SecretId=secret_identifier,
        VersionId=version_id,
        VersionStage=version_stage,
    )

    secret_value = extract_secret_from_boto3_response(
        response=response,
        base64_decode=base64_decode,
        bytes_decode=bytes_decode,
        encoding=encoding,
    )

    if memoize is True:
        os.environ[secret_identifier] = secret_value

    return secret_value
