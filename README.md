# Markdown TOC MCP Server

一个专门用于 Markdown 文档目录分析和处理的 Model Context Protocol (MCP) 服务器，为 TRAE IDE 提供强大的 Markdown 文档处理能力。

可以先阅读 [**从零构建 MCP 服务：为 TRAE IDE 添加智能 Markdown TOC 处理能力**](./docs/blog-mcp-integration.md) 来了解背后的故事！

## 1. 功能说明

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

MCP 工具唤醒方法：

```text
请使用 MCP 工具提取文档的目录结构。
```

或者直接：

```text
请提取文档的目录结构
```

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
│   └── trae_mcp_config.json    # TRAE IDE 配置
├── src/                         # 源代码目录
│   ├── __init__.py
│   ├── markdown_toc/           # 核心模块
│   │   ├── __init__.py
│   │   └── extractor.py        # TOC 提取器
│   └── server/                 # 服务器模块
│       ├── __init__.py
│       └── mcp_server.py       # MCP 服务器主程序
├── tests/                      # 测试文件目录
│   ├── __init__.py
│   ├── fixtures/               # 测试数据
│   ├── test_*.py              # 各种测试文件
│   └── test_config.py         # 测试配置
└── docs/                       # 文档目录
    ├── setup.md               # 安装说明
    ├── usage.md               # 使用指南
    ├── testing.md             # 测试说明
    └── reports/               # 测试报告
```

---

## 3. TRAE MCP 配置

请参考 [安装说明](docs/setup.md) 进行安装和配置。

---

## 4. 测试说明

请参考 [测试说明](docs/testing.md) 进行测试。

---

## 5. 功能详细说明

### 5.1 extract_markdown_toc

从 Markdown 文档中提取目录结构。

**参数：**

- `file_path` (string, 必需): Markdown 文件路径
- `output_format` (string, 可选): 输出格式，可选值：json, text, markdown，默认为 json
- `max_depth` (integer, 可选): 最大提取深度，默认为 6
- `min_depth` (integer, 可选): 最小提取深度，默认为 1
- `include_line_numbers` (boolean, 可选): 是否包含行号，默认为 false

**示例：**

```json
{
  "name": "extract_markdown_toc",
  "arguments": {
    "file_path": "/path/to/document.md",
    "output_format": "json",
    "max_depth": 4,
    "include_line_numbers": true
  }
}
```

### 5.2 analyze_numbering_issues

分析 Markdown 文档中的编号问题。

**功能说明：**

该工具会智能识别文档中的有编号标题和无编号标题，只对有编号的标题进行编号问题分析。无编号标题（如以 emoji、中文、纯文本开头的标题）不会参与编号连续性检查，避免误报。

**参数：**

- `file_path` (string, 必需): Markdown 文件路径
- `check_types` (array, 可选): 检查类型，可选值：duplicates, discontinuous，默认为 ["duplicates", "discontinuous"]

**行为逻辑：**

- **duplicates**: 检查是否存在重复的编号（如两个 "1.1" 标题）
- **discontinuous**: 检查编号是否连续（如 "1.1" 后直接跟 "1.3"，缺少 "1.2"）
- 只分析实际有编号的标题，忽略无编号标题
- 支持多种编号格式：数字编号（1.、1.1）、中文编号（一、二）等

**示例：**

```json
{
  "name": "analyze_numbering_issues",
  "arguments": {
    "file_path": "/path/to/document.md",
    "check_types": ["duplicates", "discontinuous"]
  }
}
```

### 5.3 generate_toc

生成格式化的 TOC 内容供插入文档。

**参数：**

- `file_path` (string, 必需): Markdown 文件路径
- `format_type` (string, 可选): 输出格式，可选值：markdown, html, text，默认为 markdown
- `include_links` (boolean, 可选): 是否包含链接（仅对 markdown 格式有效），默认为 true
- `max_level` (integer, 可选): 最大包含的标题级别，默认为 6

**示例：**

```json
{
  "name": "generate_toc",
  "arguments": {
    "file_path": "/path/to/document.md",
    "format_type": "markdown",
    "include_links": true,
    "max_level": 4
  }
}
```

---

## 6. 开发和调试

### 6.1 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 代码格式化
black src/

# 代码检查
flake8 src/
mypy src/
```

### 6.2 调试模式

在 `config/config.yaml` 中启用调试模式：

```yaml
development:
  debug: true

logging:
  level: "DEBUG"
```

### 6.3 日志分析

查看详细日志：

```bash
# 查看日志文件
tail -f logs/mcp_server.log

# 或在启动时查看实时日志
./start_mcp_for_trae.sh
```

---

## 7. 常见问题

**问题：服务器启动失败**：

```bash
# 检查 Python 版本
python3 --version

# 检查依赖安装
pip list | grep mcp

# 查看错误日志
tail -f logs/mcp_server.log
```

**问题：文件权限错误**：

```bash
# 检查文件权限
ls -la start_mcp_for_trae.sh
chmod +x start_mcp_for_trae.sh
```

**问题：编码错误**：

服务器支持多种编码格式（UTF-8、GBK 等），如果遇到编码问题，请确保文件编码正确。

---
