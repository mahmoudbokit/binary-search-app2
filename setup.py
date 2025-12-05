from setuptools import setup, find_packages

setup(
    name="binary-search-app",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "redis==5.0.1",
        "pydantic==2.5.0",
    ],
)