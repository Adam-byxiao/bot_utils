#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Library Setup Script
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# 读取requirements文件
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # 移除条件标记（如 ; python_version < "3.8"）
                    if ';' in line:
                        line = line.split(';')[0].strip()
                    requirements.append(line)
    return requirements

setup(
    name="chrome-devtools-lib",
    version="1.0.0",
    author="Chrome DevTools Library Team",
    author_email="dev@example.com",
    description="一个强大且易用的Python库，用于与Chrome DevTools协议进行交互",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/chrome-devtools-lib",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.8.0",
        "websockets>=10.0",
        "typing-extensions>=4.0.0; python_version < '3.8'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "examples": [
            "colorama>=0.4.0",
            "rich>=12.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "chrome-devtools-lib=chrome_devtools_lib.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "chrome_devtools_lib": [
            "examples/*.py",
            "*.md",
        ],
    },
    keywords=[
        "chrome",
        "devtools",
        "automation",
        "testing",
        "monitoring",
        "javascript",
        "websocket",
        "async",
        "performance",
        "network",
    ],
    project_urls={
        "Bug Reports": "https://github.com/example/chrome-devtools-lib/issues",
        "Source": "https://github.com/example/chrome-devtools-lib",
        "Documentation": "https://chrome-devtools-lib.readthedocs.io/",
    },
)