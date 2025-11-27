#!/usr/bin/env python3
"""
Setup script for µACP (Micro Agent Communication Protocol) library.
"""

from setuptools import setup, find_packages
import os

def read_readme():
    """Read README.md file."""
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

def read_requirements():
    """Read requirements.txt file."""
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="miuacp",
    version="1.0.0",
    author="Arnab",
    author_email="hello@arnab.wiki",
    description="µACP: A lightweight agent communication protocol for edge-native multi-agent systems",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Arnab-m1/miuACP",
    project_urls={
        "Bug Tracker": "https://github.com/Arnab-m1/miuACP/issues",
        "Documentation": "https://github.com/Arnab-m1/miuACP#readme",
        "Source Code": "https://github.com/Arnab-m1/miuACP",
        "Changelog": "https://github.com/Arnab-m1/miuACP/blob/main/CHANGELOG.md",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: System :: Distributed Computing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
        "full": [
            "prometheus-client>=0.17.0",
            "paho-mqtt>=1.6.1",
            "aiocoap>=0.4.7",
            "cryptography>=41.0.0",
            "PyJWT>=2.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "uacp-agent=miuacp.cli:main",
            "uacp-client=miuacp.client:main",
            "uacp-server=miuacp.server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "miuacp": ["py.typed"],
    },
    zip_safe=False,
    keywords=[
        "agent", "communication", "protocol", "micro", "lightweight", "edge", "iot",
        "multi-agent", "distributed", "messaging", "pubsub", "rpc", "robustness",
        "circuit-breaker", "timeout", "resource-pool", "health-monitoring"
    ],
    platforms=["any"],
    license="MIT",
    license_files=["LICENSE"],
)
