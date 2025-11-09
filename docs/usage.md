# TRAE MCP Servers 使用指南

本文档说明如何在 TRAE IDE 中使用 Markdown MCP Servers（包含 TOC 和编辑器服务器）。

## 1. 概述

### 1.1 Markdown TOC MCP Server 功能

- **TOC 提取** - 从 Markdown 文档中提取标题结构
- **编号分析** - 检测标题编号问题（重复、不连续等）
- **TOC 生成** - 生成格式化的目录内容（Markdown、HTML、Text 格式）

### 1.2 Markdown Editor MCP Server 功能

- **SIR 转换** - Markdown 与结构化中间表示（SIR）格式双向转换
- **语义编辑** - 标题编辑、章节插入、编号重排等语义级别操作
- **文档分析** - 文档结构分析、编号问题检查、格式优化
- **智能格式化** - Markdown 文档格式化和可读性优化

---

## 2. TRAE IDE 集成

为了在 TRAE IDE 中使用 Markdown MCP Servers，请首先需要：

- 智能体选择：`Builder with MCP`

### 2.1 配置服务器

打开 TRAE IDE 的 MCP 配置页面，选择添加 -> 手工添加，然后选择相应的配置文件：

#### 2.1.1 TOC 服务器配置 (`config/toc_mcp_config.json`)

```json
{
  "mcpServers": {
    "markdown-toc": {
      "command": "/Users/wangtianqing/Project/mcp/markdown-mcp/start_mcp_for_trae.sh",
      "args": []
    }
  }
}
```

#### 2.1.2 编辑器服务器配置 (`config/editor_mcp_config.json`)

```json
{
  "mcpServers": {
    "markdown-editor": {
      "command": "/Users/wangtianqing/Project/mcp/markdown-mcp/start_mcp_for_trae.sh",
      "args": ["--editor"]
    }
  }
}
```

> **注意**：确保服务器配置中的 `command` 指向正确的启动脚本路径。

### 2.2 功能使用

#### 2.2.1 TOC 服务器功能唤醒方法

```text
请使用 MCP 工具提取文档的目录结构。
请分析文档的编号问题。
请生成文档的目录。
```

#### 2.2.2 编辑器服务器功能唤醒方法

```text
请使用 MCP 工具转换文档到 SIR 格式。
请编辑文档的标题结构。
请检查文档的编号问题。
请格式化 Markdown 文档。
请插入新的章节。
```

#### 2.2.3 具体工具调用示例

```text
请使用 extract_markdown_toc 工具提取当前文档的目录
请使用 analyze_numbering_issues 工具分析编号问题
请使用 generate_toc 工具生成目录内容
请使用 convert_to_sir 工具转换文档到 SIR 格式
请使用 semantic_edit 工具进行语义编辑
请使用 agent_edit_heading 工具编辑标题
请使用 format_markdown 工具格式化文档
```

---

## 3. 常见运维操作

```bash
# 查看 TOC 服务器日志
tail -f logs/toc_mcp_server.log

# 查看编辑器服务器日志
tail -f logs/editor_mcp_server.log

# 查看错误信息
grep ERROR logs/toc_mcp_server.log
grep ERROR logs/editor_mcp_server.log

# 监控服务器状态
ps aux | grep mcp_server

# 重启服务器
./stop_mcp_for_trae.sh
./start_mcp_for_trae.sh

# 指定端口启动（解决冲突）
python src/server/toc_mcp_server.py --port 8081
python src/server/editor_mcp_server.py --port 8082
```

---

## 4. 故障排除

### 4.1 服务器启动失败

- 检查虚拟环境是否正确激活
- 确认依赖包已安装：`pip list | grep mcp`
- 验证 Python 版本：`python --version`

### 4.2 功能调用失败

- 检查服务器日志中的错误信息
- 确认文档格式符合 Markdown 规范
- 验证服务器配置正确

### 4.3 性能问题

- 大型文档处理可能需要较长时间
- 可考虑分块处理或优化文档结构

---

更多信息请参考 [README.md](../README.md) 和 [setup.md](./setup.md)
