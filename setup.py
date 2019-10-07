import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

long_description = """
**PowerfulSeal** adds chaos to your Kubernetes clusters, so that you can detect problems in your systems as early as possible. It kills targeted pods and takes VMs up and down.

Please see the documentation at https://github.com/bloomberg/powerfulseal
"""

setup(
    name='powerfulseal',
    version='2.6.0',
    author='Mikolaj Pawlikowski',
    author_email='mikolaj@pawlikowski.pl',
    url='https://github.com/bloomberg/powerfulseal',
    packages=find_packages(),
    license=read('LICENSE'),
    description='PowerfulSeal - a powerful testing tool for Kubernetes clusters',
    long_description=long_description,
    #long_description_content_type="text/markdown",
    install_requires=[
        'ConfigArgParse>=0.11.0,<1',
        'Flask>=1.0.0,<2',
        'termcolor>=1.1.0,<2',
        'openstacksdk>=0.10.0,<1',
        'spur>=0.3.20,<1',
        'kubernetes>=8.0.1<9',
        'PyYAML>=5.1.2,<6',
        'jsonschema>=3.0.2,<4',
        'boto3>=1.5.15,<2.0.0',
        'azure-common>=1.1.23,<2.0.0',
        'azure-mgmt-resource>=2.2.0,<3.0.0',
        'azure-mgmt-network>=2.7.0,<3.0.0',
        'azure-mgmt-compute>=4.6.2,<5.0.0',
        'future>=0.16.0,<1',
        'requests>=2.21.0,<3',
        'prometheus_client>=0.3.0,<0.4.0',
        'flask-cors>=3.0.6,<4',
        'flask-swagger-ui>=3.18.0<4',
        'coloredlogs>=10.0.0,<11.0.0',
        'six>=1.12.0,<2',
        'paramiko>=2.5.0,<3',
        'google-api-python-client>=1.7.8',
        'google-auth>=1.6.2',
        'google-auth-httplib2>=0.0.3',
        'oauth2client>=4.1.3'
    ],
    extras_require={
        'testing': [
            'pytest>=3.0,<4',
            'pytest-cov>=2.5,<3',
            'mock>=2,<3',
        ]
    },
    entry_points={
        'console_scripts': [
            'seal = powerfulseal.cli.__main__:start',
            'powerfulseal = powerfulseal.cli.__main__:start',
        ]
    },
    classifiers=[
	    'Development Status :: 4 - Beta',
	    'Intended Audience :: Developers',
	    'Topic :: Software Development :: Test Tools',
	    'Programming Language :: Python :: 3',
    ],
    python_requires='>=3',
    include_package_data=True,
)
