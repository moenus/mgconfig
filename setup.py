# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from setuptools import setup, find_packages

# Read README with explicit UTF-8 encoding
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mgconfig",
    version="0.2.2-dev",  # Will be updated by bump2version
    author="Moenus",
    description="A flexible, lightweight and declarative configuration system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "tzlocal>=5.0,<6.0",
        "PyYAML>=6.0,<7.0",
    ],
    python_requires='>=3.7',
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "build>=1.0.0",
            "wheel>=0.41.0",
            "setuptools>=61.0"
        ],
        "docs": ["sphinx>=7.0"],
    }
)