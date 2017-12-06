from setuptools import setup, find_packages


setup(
    name='powerfulseal',
    version='2.0.0',
    author='Mikolaj Pawlikowski',
    packages=find_packages(),
    license=open('LICENSE').read(),
    description='Powerfulseal kubernetes reliablity tester',
    long_description=open('README.md').read(),
    install_requires=[
        'ConfigArgParse>=0.11.0,<1',
        'Flask>=0.12.2,<0.13',
        'termcolor>=1.1.0,<2',
        'openstacksdk>=0.9.18,<1',
        'spur>=0.3.20,<1',
        'kubernetes>=1.0.0,<2',
        'PyYAML>=3.12,<4',
        'jsonschema>=2.6.0,<3',
    ],
    entry_points={
        'console_scripts': [
            'seal = powerfulseal.cli.__main__:main',
            'powerfulseal = powerfulseal.cli.__main__:main',
        ]
    },
    include_package_data=True,
)
