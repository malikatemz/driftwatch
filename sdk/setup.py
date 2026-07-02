from setuptools import setup, find_packages

setup(
    name="driftwatch",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.0",
        "click>=8.0",
        "python-dotenv>=1.0",
        "nest-asyncio>=1.6.0",
    ],
    python_requires=">=3.10",
    description="Security monitoring for developer APIs",
    author="Driftwatch",
    url="https://driftwatch.io",
    entry_points={"console_scripts": ["driftwatch=driftwatch.cli:cli"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
