from setuptools import setup, find_packages

setup(
    name="flowweaver-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_packages=["pydantic>=2.0.0", "pyyaml>=6.0"],
    extras_require={
        "polars": ["polars>=1.0.0"],
        "arrow": ["pyarrow>=14.0.0"],
        "duckdb": ["duckdb>=0.9.0"],
    },
    entry_points={
        "console_scripts": [
            "flowweaver=flowweaver.sdk.cli:main",
        ]
    },
    author="FlowWeaver Team",
    description="Core developer SDK for writing FlowWeaver nodes and plugins",
    python_requires=">=3.8",
)
