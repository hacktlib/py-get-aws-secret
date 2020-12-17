import base64
import binascii
import json
import os
from unittest import mock

import boto3
import botocore
import pytest

from get_aws_secret import (
    constants as c,
    extract_secret_from_boto3_response as extract_secret,
    get_client,
    get_secret,
    get_secret_fix_args,
    new_boto3_client,
    return_secret,
)


UNEXPECTED_BYTES_DECODE_ERROR = 'Unexpected bytes decoding AttributeError'
UNEXPECTED_BASE64_DECODE_ERROR = 'Unexpected base64 decoding binascii.Error'


@pytest.fixture(autouse=True)
def inject_aws_environment_vars():
    aws_env_vars = {
        'AWS_DEFAULT_REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': 'LOCAL_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY': 'LOCAL_SECRET_ACCESS_KEY',
    }

    with mock.patch.dict(os.environ, aws_env_vars):
        yield


@pytest.fixture
def secret_key():
    return 'SECRET_KEY'


@pytest.fixture
def secret_key_json():
    return 'SECRET_KEY_JSON'


@pytest.fixture
def secret_key_env():
    return 'SECRET_ENV_VAR_KEY'


@pytest.fixture
def secret_str():
    return 'MY_DUMMY_SECRET'


@pytest.fixture
def secret_key_env_json(secret_key_env):
    return f'{secret_key_env}_JSON'


@pytest.fixture
def secret_str_json():
    return '{"hello": "world"}'


@pytest.fixture
def secret_base64(secret_str):
    return base64.b64encode(secret_str.encode('utf-8'))


@pytest.fixture
def secret_env_var_dict(
        secret_key_env,
        secret_key_env_json,
        secret_str,
        secret_str_json,
        ):
    return {
        secret_key_env: secret_str,
        secret_key_env_json: secret_str_json,
    }


@pytest.fixture
def mock_secret_str_response(secret_str):
    return {'SecretString': secret_str}


@pytest.fixture
def mock_secret_str_json_response(secret_str_json):
    return {'SecretString': secret_str_json}


@pytest.fixture
def mock_secret_base64_response(secret_base64):
    return {'SecretBinary': secret_base64}


def test_get_client():
    client = get_client(None)

    assert isinstance(client, botocore.client.BaseClient)
    assert client._service_model.service_name == 'secretsmanager'

    custom_client = boto3.client('secretsmanager', region_name='my-region-1')

    client = get_client(custom_client)

    assert client == custom_client


def test_get_new_boto3_client():
    client = new_boto3_client()

    assert isinstance(client, botocore.client.BaseClient)
    assert client._service_model.service_name == 'secretsmanager'


def test_extract_secret_from_boto3_response(secret_str, secret_base64):
    secret_str_resp = {'SecretString': secret_str}
    secret_bin_resp = {'SecretBinary': secret_base64}

    # Default arguments
    assert extract_secret(secret_str_resp) == secret_str
    assert extract_secret(secret_bin_resp) == secret_str

    # Without decoding from bytes to string
    no_bytes_decoding = extract_secret(secret_bin_resp, bytes_decode=False)
    assert type(no_bytes_decoding) is bytes
    try:
        no_bytes_decoding.decode(c.DEFAULT_ENCODING)
    except AttributeError:
        pytest.fail(UNEXPECTED_BYTES_DECODE_ERROR)

    # Without base64 decoding
    no_b64_decoding = extract_secret(secret_bin_resp, base64_decode=False)
    assert type(no_b64_decoding) is str
    try:
        base64.b64decode(no_b64_decoding)
    except binascii.Error:
        pytest.fail(UNEXPECTED_BASE64_DECODE_ERROR)

    # Without any decoding
    no_decoding = extract_secret(
        secret_bin_resp,
        base64_decode=False,
        bytes_decode=False,
    )
    assert type(no_decoding) is bytes
    try:
        base64.b64decode(no_b64_decoding)
    except binascii.Error:
        pytest.fail(UNEXPECTED_BASE64_DECODE_ERROR)
    except AttributeError:
        pytest.fail(UNEXPECTED_BYTES_DECODE_ERROR)


def test_get_secret_from_env_var(
        mock_secret_str_response,
        secret_env_var_dict,
        secret_str,
        secret_key_env,
        ):
    with mock.patch.dict(os.environ, secret_env_var_dict):
        assert secret_key_env in os.environ.keys()
        assert os.environ[secret_key_env] == \
            secret_env_var_dict[secret_key_env]

        client = mock.Mock()
        client.get_secret_value = mock.Mock(
            return_value=mock_secret_str_response,
        )

        secret = get_secret(secret_key_env, client=client, memoize=True)

        client.get_secret_value.assert_not_called()

        assert secret == secret_str


def test_get_secret_from_env_var_load_json(
        mock_secret_str_json_response,
        secret_env_var_dict,
        secret_key_env_json,
        secret_str_json,
):
    with mock.patch.dict(os.environ, secret_env_var_dict):
        assert secret_key_env_json in os.environ.keys()
        assert os.environ[secret_key_env_json] == \
            secret_env_var_dict[secret_key_env_json]

        client = mock.Mock()
        client.get_secret_value = mock.Mock(
            return_value=mock_secret_str_json_response,
        )

        secret = get_secret(secret_key_env_json, client=client, memoize=True)

        client.get_secret_value.assert_not_called()

        assert secret == json.loads(secret_str_json)


@mock.patch('get_aws_secret.get_client')
def test_get_secret_and_memoization(
        get_client,
        secret_key_env,
        secret_str,
        ):
    with mock.patch.dict(os.environ, {}):
        secret_key_memo = f'{secret_key_env}_MEMOIZED'
        secret_str_memo = f'{secret_str}_MEMOIZED'

        assert secret_key_memo not in os.environ.keys()

        client = mock.Mock()
        client.get_secret_value = mock.Mock(
            return_value={'SecretString': secret_str_memo}
        )
        get_client.return_value = client

        # Confirm that it's not memoizing when not requested
        secret = get_secret(secret_key_memo, client=client)
        assert secret == secret_str_memo
        assert secret_key_memo not in os.environ.keys()

        # Verify whether it's memoizing when requested to do so
        secret = get_secret(secret_key_memo, client=client, memoize=True)
        assert secret == secret_str_memo
        assert secret_key_memo in os.environ.keys()
        assert os.environ[secret_key_memo] == secret_str_memo

        new_client = mock.Mock()
        new_client.get_string_value = mock.Mock(
            return_value={'SecretString': secret_str_memo},
        )
        get_client.return_value = new_client

        # Confirm that it retrieves from env vars after memoization
        secret = get_secret(secret_key_memo, client=new_client, memoize=True)
        new_client.assert_not_called()
        assert secret == secret_str_memo


@mock.patch('get_aws_secret.get_client')
def test_get_secret_client_mock(
        get_client,
        mock_secret_str_response,
        secret_str,
        secret_key,
        ):
    client = mock.Mock()
    client.get_secret_value = mock.Mock(return_value=mock_secret_str_response)
    get_client.return_value = client

    secret = get_secret(secret_key, client=client)

    get_client.assert_called_with(client)

    client.get_secret_value.assert_called_with(
        SecretId=secret_key,
        VersionId=c.DEFAULT_SECRET_VERSION_ID,
        VersionStage=c.DEFAULT_SECRET_VERSION_STAGE,
    )
    assert secret == secret_str


@mock.patch('get_aws_secret.get_client')
def test_get_secret_load_json_client_mock(
        get_client,
        mock_secret_str_json_response,
        secret_str_json,
        secret_key_json,
        ):
    client = mock.Mock()
    client.get_secret_value = mock.Mock(
        return_value=mock_secret_str_json_response,
    )
    get_client.return_value = client

    secret = get_secret(secret_key_json, client=client)

    get_client.assert_called_with(client)

    client.get_secret_value.assert_called_with(
        SecretId=secret_key_json,
        VersionId=c.DEFAULT_SECRET_VERSION_ID,
        VersionStage=c.DEFAULT_SECRET_VERSION_STAGE,
    )
    assert secret == json.loads(secret_str_json)


@mock.patch('get_aws_secret.get_secret')
def test_get_secret_fix_args(get_secret, secret_str):
    with mock.patch.dict(os.environ, {}):
        client = mock.Mock()
        get_secret.return_value = secret_str

        secret_key = 'DUMMY_SECRET'
        version_id = 1
        version_stage = 2
        get_secret_kwargs = {
            'memoize': True,
            'client': client,
            'version_id': version_id,
            'version_stage': version_stage,
        }

        get_secret_ = get_secret_fix_args(**get_secret_kwargs)

        secret = get_secret_(secret_key)

        get_secret.assert_called_once_with(secret_key, **get_secret_kwargs)
        assert secret == secret_str


def test_return_secret():
    secret = return_secret('data', load_json=False)
    assert secret == 'data'

    try:
        secret = return_secret('data', load_json=True)
    except json.decoder.JSONDecodeError:
        pytest.fail('Unexpected JSONDecodeError')
    else:
        assert secret == 'data'

    secret = return_secret('{"hello": "world"}', load_json=True)
    assert type(secret) is dict
    assert 'hello' in secret.keys()
    assert secret['hello'] == 'world'

    secret = return_secret('{"hello": "world"}', load_json=False)
    assert type(secret) == str
    assert secret == '{"hello": "world"}'
