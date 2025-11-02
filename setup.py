#!/usr/bin/env python3
"""
Markdown TOC MCP Server 安装配置

用于安装和配置 Markdown TOC MCP Server 包。
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README 文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# 读取 requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        "mcp>=0.1.0",
        "markdown>=3.4.0",
        "python-markdown>=3.4.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "regex>=2023.6.0",
        "chardet>=5.1.0",
        "aiofiles>=23.1.0",
        "pyyaml>=6.0"
    ]

setup(
    name="markdown-toc-mcp-server",
    version="2.0.0",
    author="TRAE AI Assistant",
    author_email="assistant@trae.ai",
    description="Markdown TOC MCP Server - 专门用于 Markdown 文档目录分析和处理的 MCP 服务器，提供 TOC 提取、编号分析和生成 TOC 目录功能",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trae-ai/markdown-toc-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Technical Writers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "coverage>=7.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "markdown-toc-mcp-server=mcp_server:main",
            "start-markdown-toc-server=mcp_server:start_server",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt", "*.md"],
    },
    zip_safe=False,
    keywords=[
        "mcp",
        "model-context-protocol",
        "markdown",
        "toc",
        "table-of-contents",
        "documentation",
        "analysis",
        "numbering"
    ],
    project_urls={
        "Bug Reports": "https://github.com/ForceInjection/markdown-mcp/issues",
        "Source": "https://github.com/ForceInjection/markdown-mcp",
        "Documentation": "https://github.com/ForceInjection/markdown-mcp/blob/main/README.md",
    },
)