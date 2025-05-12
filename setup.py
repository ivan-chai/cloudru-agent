import os
import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    name="cloudru-agent",
    version="0.0.1",
    author="Ivan Karpukhin",
    author_email="karpuhini@yandex.ru",
    description="A simple tool for dynamic allocation of agents on cloud.ru.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(include=["cloudru_agent", "cloudru_agent.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "client_lib",
        "wandb"
    ]
)
