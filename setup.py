from setuptools import find_packages, setup
import pathlib


here = pathlib.Path(__file__).parent.resolve()

# Get long version of description from README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

# Developer-mode PyPi requirements
dev_requirements = [
    'pytest>=6.2.0',
    'coverage>=5.3',
    'coverage-badge>=1.0.1',
    'wheel>=0.36.2',
    'flake8>=3.8.4',
    'autopep8>=1.5.4',
]

# Publisher-mode PyPi requirements
pub_requirements = dev_requirements + ['twine>=3.2.0']

setup(
    name='get-aws-secret',
    version='0.2.0b3',
    description='Simplify retrieval of secrets from AWS SecretsManager. ' +
                'Optionally auto-memoize secrets in environment variables ' +
                'to improve performance and reduce costs.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/hacktlib/py-get-aws-secret/wiki',
    author='Hackt.app',
    author_email='opensource@hackt.app',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.6, <4',
    install_requires=[
        'boto3>=1.16.36',
    ],
    extras_require={
        'dev': dev_requirements,
        'pub': pub_requirements,
    },
    project_urls={
        'Bug Reports': 'https://github.com/hacktlib/py-get-aws-secret/issues',
        'Say Thanks!': 'http://lib.hackt.app',
        'Source': 'https://github.com/hacktlib/py-get-aws-secret/',
    },
)
