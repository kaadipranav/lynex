from setuptools import setup, find_packages

setup(
    name="watchllm",
    version="0.1.0",
    description="Python SDK for WatchLLM",
    author="WatchLLM Team",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
        "tenacity>=8.0.0",
    ],
    python_requires=">=3.8",
)
