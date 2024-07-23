from setuptools import setup, find_packages

setup(
    name="spot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["anyio", "httpx"],
    description="SDK for Spot",
    author="",
    author_email="",
    url="https://github.com/Spot-Network/spot-sdk",
)
