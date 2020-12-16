# Get AWS Secret

![Test Coverage](https://raw.githubusercontent.com/hacktlib/py-get-aws-secret/main/coverage.svg)
![PyPI](https://img.shields.io/pypi/v/get-aws-secret)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Requirements Status](https://requires.io/github/hacktlib/py-get-aws-secret/requirements.svg?branch=main)](https://requires.io/github/hacktlib/py-get-aws-secret/requirements/?branch=main)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-lightgrey)](https://github.com/hhatto/autopep8/)
[![Code Formatter](https://img.shields.io/badge/formatter-autopep8-lightgrey)](https://github.com/hhatto/autopep8/)
[![Test Framework](https://img.shields.io/badge/testing-pytest-lightgrey)](https://github.com/pytest-dev/pytest/)


> We built this library in [Hackt](https://hackt.app) to support local development of internal projects and [public apps in our catalog](https://hackt.app/catalog). Learn more about other open-source libraries on [lib.hackt.app](https://lib.hackt.app/).

---


# Runtime support

![Python Logo](https://logo.clearbit.com/python.org?size=120)

> This is the Python runtime library, compatible with Python3.6+. Currently there isn't support for other runtimes. A Javascript/nodejs version is planned, but unscheduled.

---


# Installation and Usage

Install with pip: `pip install get-aws-secret`

```python
from get_aws_secret import get_secret

secret_val = get_secret('MY_SECRET_DATA')
```

The `get_secret` method also accepts a secret ARN:

```python
secret_val = get_secret('arn:aws:secretsmanager:us-east-1:123456789012:secret:MY_SECRET_DATA')
```


## Memoization

The library can automatically set the secret as environment variable and retrieve from there in subsequent requests.

```python
from get_aws_secret import get_secret

secret_val = get_secret('MY_SECRET_DATA', memoize=True)
```

In the first run, setting `memoize=True` is equivalent to running `os.environ['MY_SECRET_DATA'] = secret_val` after retrieving the secret.

In subsequent calls with `memoize=True`, the function will find `MY_SECRET_DATA` in `os.environ` and retrieve it locally . In other words, it won't hit the AWS endpoints (saves a few milliseconds and cents).

It's possible to set the behavior of `memoize=True` (in fact, any other get_value argument) as the default for all requests without explicit argument:

```python
from get_aws_secret import get_secret_fix_args

get_secret = get_secret_fix_args(memoize=True)

secret_val = get_secret('MY_SECRET_DATA')
```


## Custom `boto3.client`

Optionally, set a custom `boto3.client` with:

```python
import boto3
from get_aws_secret import get_secret_fix_args

client = boto3.client('secretsmanager', region_name='my-region-1')

get_secret = get_secret_fix_args(client=client)

secret_val = get_secret('MY_SECRET_DATA')
```

----

## License

This library is licensed under [Apache 2.0](https://raw.githubusercontent.com/hacktlib/py-get-aws-secret/main/LICENSE).

---

## Contributor guide

Please check out guidelines in the [repository wiki](https://github.com/hacktlib/py-get-aws-secret/wiki).

---

## Acknowledgements

Published & supported by [**Hackt App**](https://hackt.app)

Logos provided by [**Clearbit**](https://clearbit.com)
