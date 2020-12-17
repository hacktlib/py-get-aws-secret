import base64
from functools import partial
import json
import os
from typing import Optional, Union

import boto3
import botocore

from get_aws_secret import constants as c


def get_secret_fix_args(*args, **kwargs):
    return partial(get_secret, *args, **kwargs)


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


def return_secret(
        secret_value: str,
        load_json: bool,
        ) -> Union[str, dict, list]:
    if load_json is not True:
        return secret_value

    try:
        return json.loads(secret_value)
    except (json.decoder.JSONDecodeError, TypeError):
        return secret_value


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

        load_json: Optional[bool] = True,
        ) -> str:
    if memoize is True and secret_identifier in os.environ.keys():
        return return_secret(os.environ[secret_identifier], load_json)

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

    return return_secret(secret_value, load_json)
