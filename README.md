# Markdown MCP Servers

一套专门用于 Markdown 文档处理的 Model Context Protocol (MCP) 服务器集合，为 TRAE IDE 提供强大的 Markdown 文档处理能力。包含 TOC 服务器和编辑器服务器两个组件。

可以先阅读 [**从零构建 MCP 服务：为 TRAE IDE 添加智能 Markdown TOC 处理能力**](./docs/blog-mcp-integration.md) 以及[**智能体如何高效处理 Markdown：结构化解析与语义编辑方案**](./docs/markdown-agent.md)来了解背后的故事！

## 1. 功能说明

### 1.1 Markdown TOC MCP Server

| **功能模块**     | **主要特性**           | **详细说明**                  |
| ---------------- | ---------------------- | ----------------------------- |
| **提取文档目录** | 自动识别 Markdown 标题 | 智能解析文档中的各级标题结构  |
|                  | 生成层级目录结构       | 构建完整的目录层次关系        |
|                  | 包含行号信息           | 提供精确的标题位置信息        |
| **检查编号问题** | 检测重复编号           | 识别文档中重复的章节编号      |
|                  | 发现不连续编号         | 发现跳跃或缺失的编号序列      |
|                  | 分析格式问题           | 检查编号格式的一致性          |
| **生成目录内容** | 创建格式化 TOC         | 生成美观的目录内容            |
|                  | 支持多种输出格式       | 提供 Markdown、HTML、文本格式 |
|                  | 可自定义深度           | 灵活控制目录显示层级          |

### 1.2 Markdown Editor MCP Server

| **功能模块** | **主要特性** | **详细说明**                 |
| ------------ | ------------ | ---------------------------- |
| **SIR 转换** | 双向格式转换 | Markdown ↔ 结构化中间表示    |
|              | 格式保持     | 转换过程中保持文档结构完整性 |
|              | 高性能处理   | 支持大型文档的高效转换       |
| **语义编辑** | 智能标题编辑 | 支持标题文本和级别的修改     |
|              | 章节插入     | 在指定位置插入新的章节       |
|              | 编号重排     | 自动重新编号文档标题         |
| **文档分析** | 结构分析     | 分析文档结构和完整性         |
|              | 编号检查     | 检测编号重复和不连续问题     |
|              | 格式优化     | 优化文档格式和可读性         |

---

## 2. 项目结构

```text
markdown-mcp/
├── README.md                    # 项目说明文档
├── LICENSE                      # 许可证文件
├── requirements.txt             # Python 依赖包
├── setup.py                     # 安装配置文件
├── run_tests.py                 # 测试运行脚本
├── start_mcp_for_trae.sh       # TRAE IDE 启动脚本
├── stop_mcp_for_trae.sh        # TRAE IDE 停止脚本
├── config/                      # 配置文件目录
│   ├── config.yaml             # 主配置文件
│   ├── toc_mcp_config.json     # TOC 服务器 TRAE IDE 配置
│   └── editor_mcp_config.json  # 编辑器服务器 TRAE IDE 配置
├── src/                         # 源代码目录
│   ├── __init__.py
│   ├── markdown_toc/           # TOC 核心模块
│   │   ├── __init__.py
│   │   └── extractor.py        # TOC 提取器
│   ├── markdown_editor/        # 编辑器核心模块
│   │   ├── __init__.py
│   │   ├── ast_parser.py       # AST 解析器
│   │   ├── semantic_editor.py  # 语义编辑器
│   │   └── format_optimizer.py # 格式优化器
│   └── server/                 # 服务器模块
│       ├── __init__.py
│       ├── toc_mcp_server.py   # TOC MCP 服务器主程序
│       └── editor_mcp_server.py # 编辑器 MCP 服务器主程序
├── tests/                      # 测试文件目录
│   ├── __init__.py
│   ├── fixtures/               # 测试数据
│   ├── toc/                    # TOC 服务器测试
│   │   ├── test_extractor.py   # 提取器测试
│   │   └── test_integration.py # 集成测试
│   ├── editor/                 # 编辑器服务器测试
│   │   ├── test_ast_parser.py  # AST 解析器测试
│   │   ├── test_semantic_editor.py # 语义编辑器测试
│   │   └── test_format_optimizer.py # 格式优化器测试
│   └── test_config.py         # 测试配置
└── docs/                       # 文档目录
    ├── setup.md               # 安装说明
    ├── usage.md               # 使用指南
    ├── testing.md             # 测试说明
    └── reports/               # 测试报告
```

---

## 3. 环境配置

请参考 [安装说明](docs/setup.md) 进行环境配置。

---

## 4. 测试说明

请参考 [测试说明](docs/testing.md) 进行测试。

---

## 5. 使用说明

请参考 [使用说明](docs/usage.md) 进行配置。

---
