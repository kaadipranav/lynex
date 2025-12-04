from setuptools import setup, find_packages

setup(
    name="lynex",
    version="0.1.0",
    description="Python SDK for Lynex",
    author="Lynex Team",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.8",
)
