from setuptools import setup

setup(
    name='BattleAgentBench',
    version='0.1',
    description='whatever',
    install_requires=[
        'pygame==2.5.2',
        'openai==0.28.1',
        'tenacity==8.5'
    ],
    include_package_data=True,
)
