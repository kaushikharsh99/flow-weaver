from setuptools import setup, find_packages

setup(
    name="flowweaver-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_packages=["pydantic>=2.0.0"],
    author="FlowWeaver Team",
    description="Core developer SDK for writing FlowWeaver nodes and plugins",
    python_requires=">=3.8",
)
