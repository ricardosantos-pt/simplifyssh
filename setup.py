from setuptools import setup

setup(
    name='simplifyssh',
    version='0.7.0',
    packages=['simplifyssh'],
    install_requires=[
        'paramiko',
        'psutil'
    ],
    entry_points={
        'console_scripts': [
            'simplifyssh = simplifyssh.__main__:main'
        ]
    }
)
