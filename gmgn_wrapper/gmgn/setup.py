from setuptools import setup, find_packages

setup(
    name="gmgn-wrapper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "tls-client",
        "fake-useragent",
        "requests",
        "tabulate",
    ],
)