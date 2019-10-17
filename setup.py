from setuptools import setup

setup(
    name='simplifyssh',
    version='0.2.2',
    packages=['simplifyssh'],
    install_requires=[
        'paramiko'
    ],
    entry_points={
        'console_scripts': [
            'simplifyssh = simplifyssh.__main__:main'
        ]
    })
