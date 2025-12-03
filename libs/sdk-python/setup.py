from setuptools import setup, find_packages

setup(
    name="sentryai",
    version="0.1.0",
    description="Python SDK for Sentry for AI",
    author="SentryAI Team",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.8",
)
