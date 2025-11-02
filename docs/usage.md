# TRAE MCP Server 使用指南

本文档说明如何在 TRAE IDE 中使用 Markdown TOC MCP 服务器。

## 1. 概述

Markdown TOC MCP Server 为 TRAE IDE 提供 Markdown 文档目录处理功能：

- **TOC 提取** - 从 Markdown 文档中提取标题结构
- **编号分析** - 检测标题编号问题
- **TOC 生成** - 生成格式化的目录内容

---

## 2. TRAE IDE 集成

为了在 TRAE IDE 中使用 Markdown TOC MCP 服务器，请首先需要：

- 智能体选择：`Builder with MCP`

### 2.1 配置服务器

打开 MCP 配置页面，选择添加 -> 手工添加，然后将[Markdown MCP 服务器配置](./../config/trae_mcp_config.json) json 内容复制到输入框中并保存。

> **注意**：确保服务器配置中的 `command` 指向正确的启动脚本路径。

### 2.2 功能使用

MCP 工具唤醒方法：

```text
请使用 MCP 工具提取文档的目录结构。
```

或者直接：

```text
请提取文档的目录结构
```

---

## 3. 常见运维操作

```bash
# 查看服务器日志
tail -f logs/mcp_server.log

# 查看错误信息
grep ERROR logs/mcp_server.log
```

---

更多信息请参考 [README.md](../README.md)
