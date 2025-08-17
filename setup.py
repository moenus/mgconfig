# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from setuptools import setup, find_packages

setup(
    name="mgconfig",
    version="0.1",
    author="Michael Gross",
    description="A lightweight Python configuration system driven by declarative YAML definitions",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "tzlocal>=5.0,<6.0",
        "python-dotenv>=1.0.0,<2.0",
        "PyYAML>=6.0,<7.0",
    ],
    python_requires='>=3.8',
    extras_require={
        "dev": ["pytest>=7.0", "black>=23.0"],
        "docs": ["sphinx>=7.0"],
    }
)
