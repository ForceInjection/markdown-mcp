#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Editor MCP Server

专门为 Markdown 文档语义编辑设计的 MCP 服务器，
基于 SIR (Structured Intermediate Representation) 提供语义级别的编辑操作。

## 核心功能模块

### 1. SIR 转换 (Structured Intermediate Representation)
- **convert_to_sir**: 将 Markdown 转换为 SIR (Structured Intermediate Representation) 格式
- **convert_to_markdown**: 将 SIR 格式转换回 Markdown

### 2. 语义编辑 (Semantic Editing)
- **semantic_edit**: 对 Markdown 文档进行语义级别的编辑操作，支持插入、更新、删除和移动等操作
- **agent_edit_heading**: 编辑 Markdown 文档中的标题，支持修改标题文本和级别
- **agent_renumber_headings**: 重新编号 Markdown 文档中的所有标题，支持多种编号方案
- **agent_insert_section**: 在 Markdown 文档中插入新的章节，支持多种插入位置和标题级别

### 3. 文档分析与编号检查
- **analyze_document**: 分析 Markdown 文档的结构和内容，提供详细的文档分析报告
- **agent_check_numbering**: 检查 Markdown 文档中的标题编号问题，包括重复、不连续、无效和缺失编号
- **format_markdown**: 格式化 Markdown 文档，优化文档格式和可读性

## 技术特性

- **智能体友好**: 专为 AI 智能体设计的语义接口，支持精确的文档操作
- **高性能**: 优化的解析和渲染算法，支持大型文档处理
- **可扩展**: 模块化架构，易于添加新的编辑操作和分析功能
- **可靠性**: 完善的错误处理和恢复机制，确保操作安全性
- **兼容性**: 支持标准 Markdown 语法和常见扩展语法
"""

import asyncio
import json
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from markdown_editor.semantic_editor import (
    SemanticEditor, create_editor_from_markdown, EditOperation, EditResult
)
from markdown_editor.sir_converter import convert_markdown_to_sir
from markdown_editor.sir_renderer import render_sir_to_markdown

# 配置日志
def setup_logging():
    """设置日志配置，包括文件日志和控制台日志"""
    # 创建日志目录
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 文件日志处理器（轮转日志）
    log_file = log_dir / "editor_mcp_server.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 控制台日志处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

# 初始化日志
logger = setup_logging()


class MarkdownEditorMCPServer:
    """Markdown Editor MCP 服务器主类"""
    
    def __init__(self):
        """初始化 MCP 服务器"""
        logger.info("正在初始化 Markdown Editor MCP 服务器...")
        self.server = Server("markdown-editor-mcp-server")
        self.setup_handlers()
        logger.info("MCP 服务器初始化完成")
        
    def setup_handlers(self):
        """设置请求处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用工具列表"""
            return [
                Tool(
                    name="convert_to_sir",
                    description="将 Markdown 转换为 SIR (Structured Intermediate Representation) 格式",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "output_format": {
                                "type": "string",
                                "description": "输出格式",
                                "enum": ["json", "minified"],
                                "default": "json",
                                "required": False
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="convert_to_markdown",
                    description="将 SIR 格式转换回 Markdown",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sir_content": {
                                "type": "string",
                                "description": "SIR 格式的 JSON 内容",
                                "required": True
                            },
                            "output_format": {
                                "type": "string",
                                "description": "输出格式",
                                "enum": ["markdown", "pretty"],
                                "default": "markdown",
                                "required": False
                            }
                        },
                        "required": ["sir_content"]
                    }
                ),
                Tool(
                    name="semantic_edit",
                    description="对 Markdown 文档进行语义级别的编辑操作，支持插入、更新、删除和移动等操作",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "operation": {
                                "type": "string",
                                "description": "编辑操作类型",
                                "enum": ["insert", "update", "delete", "move"],
                                "required": True
                            },
                            "target": {
                                "type": "string",
                                "description": "操作目标（如标题、段落、列表项等）",
                                "required": True
                            },
                            "content": {
                                "type": "string",
                                "description": "新的内容（对于插入和更新操作）",
                                "required": False
                            },
                            "position": {
                                "type": "string",
                                "description": "位置信息（对于插入和移动操作，如 'before section1' 或 'after heading2'）",
                                "required": False
                            }
                        },
                        "required": ["file_path", "operation", "target"]
                    }
                ),
                Tool(
                    name="agent_edit_heading",
                    description="编辑 Markdown 文档中的标题，支持修改标题文本和级别",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "heading_id": {
                                "type": "string",
                                "description": "标题标识符（可以是标题文本、编号或位置索引）",
                                "required": True
                            },
                            "new_text": {
                                "type": "string",
                                "description": "新的标题文本",
                                "required": True
                            },
                            "new_level": {
                                "type": "integer",
                                "description": "新的标题级别（1-6），可选参数",
                                "minimum": 1,
                                "maximum": 6,
                                "required": False
                            }
                        },
                        "required": ["file_path", "heading_id", "new_text"]
                    }
                ),
                Tool(
                    name="agent_renumber_headings",
                    description="重新编号 Markdown 文档中的所有标题，支持多种编号方案",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "numbering_scheme": {
                                "type": "string",
                                "description": "编号方案",
                                "enum": ["decimal", "nested", "alphabetical", "roman"],
                                "default": "decimal",
                                "required": False
                            },
                            "start_from": {
                                "type": "integer",
                                "description": "起始编号",
                                "default": 1,
                                "minimum": 1,
                                "required": False
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="agent_insert_section",
                    description="在 Markdown 文档中插入新的章节，支持多种插入位置和标题级别",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "section_title": {
                                "type": "string",
                                "description": "章节标题",
                                "required": True
                            },
                            "section_content": {
                                "type": "string",
                                "description": "章节内容",
                                "required": True
                            },
                            "position": {
                                "type": "string",
                                "description": "插入位置",
                                "enum": ["beginning", "end", "after", "before"],
                                "default": "end",
                                "required": False
                            },
                            "reference_section": {
                                "type": "string",
                                "description": "参考章节标题或标识符（用于 after/before 位置）",
                                "required": False
                            },
                            "heading_level": {
                                "type": "integer",
                                "description": "标题级别（1-6）",
                                "minimum": 1,
                                "maximum": 6,
                                "default": 2,
                                "required": False
                            }
                        },
                        "required": ["file_path", "section_title", "section_content"]
                    }
                ),
                Tool(
                    name="agent_check_numbering",
                    description="检查 Markdown 文档中的标题编号问题，包括重复、不连续、无效和缺失编号",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "check_types": {
                                "type": "array",
                                "description": "检查的问题类型",
                                "items": {
                                    "type": "string",
                                    "enum": ["duplicates", "discontinuous", "invalid", "missing"]
                                },
                                "default": ["duplicates", "discontinuous"],
                                "required": False
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="analyze_document",
                    description="分析 Markdown 文档的结构和内容，提供详细的文档分析报告",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "analysis_type": {
                                "type": "string",
                                "description": "分析类型",
                                "enum": ["structure", "content", "completeness", "all"],
                                "default": "all",
                                "required": False
                            },
                            "include_statistics": {
                                "type": "boolean",
                                "description": "是否包含统计信息",
                                "default": True,
                                "required": False
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="format_markdown",
                    description="格式化 Markdown 文档，优化文档格式和可读性",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径",
                                "required": True
                            },
                            "format_options": {
                                "type": "object",
                                "description": "格式化选项",
                                "properties": {
                                    "indent_size": {
                                        "type": "integer",
                                        "description": "缩进大小",
                                        "default": 2,
                                        "required": False
                                    },
                                    "max_line_length": {
                                        "type": "integer",
                                        "description": "最大行长度",
                                        "default": 80,
                                        "required": False
                                    },
                                    "preserve_line_breaks": {
                                        "type": "boolean",
                                        "description": "是否保留换行符",
                                        "default": False,
                                        "required": False
                                    }
                                },
                                "default": {},
                                "required": False
                            }
                        },
                        "required": ["file_path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            """处理工具调用"""
            logger.info(f"收到工具调用请求: {name}")
            logger.debug(f"工具参数: {arguments}")
            
            try:
                if name == "convert_to_sir":
                    result = await self._convert_to_sir(arguments)
                    logger.info(f"SIR 转换完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "convert_to_markdown":
                    result = await self._convert_to_markdown(arguments)
                    logger.info("Markdown 转换完成")
                    return result
                elif name == "semantic_edit":
                    result = await self._semantic_edit(arguments)
                    logger.info(f"语义编辑完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "analyze_document":
                    result = await self._analyze_document(arguments)
                    logger.info(f"文档分析完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "format_markdown":
                    result = await self._format_markdown(arguments)
                    logger.info(f"文档格式化完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "agent_edit_heading":
                    result = await self._agent_edit_heading(arguments)
                    logger.info(f"智能体标题编辑完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "agent_renumber_headings":
                    result = await self._agent_renumber_headings(arguments)
                    logger.info(f"智能体重编号完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "agent_insert_section":
                    result = await self._agent_insert_section(arguments)
                    logger.info(f"智能体插入章节完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "agent_check_numbering":
                    result = await self._agent_check_numbering(arguments)
                    logger.info(f"智能体编号检查完成: {arguments.get('file_path', 'unknown')}")
                    return result
                else:
                    logger.warning(f"未知工具调用: {name}")
                    raise ValueError(f"未知工具: {name}")
                    
            except Exception as e:
                logger.error(f"工具调用错误 {name}: {e}", exc_info=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"错误: {str(e)}")],
                    isError=True
                )
    
    async def _convert_to_sir(self, arguments: Dict[str, Any]) -> CallToolResult:
        """将 Markdown 转换为 SIR 格式"""
        file_path = arguments["file_path"]
        output_format = arguments.get("output_format", "json")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 转换为 SIR
            sir_doc = convert_markdown_to_sir(content, file_path)
            
            # 格式化输出
            if output_format == "minified":
                result_content = json.dumps(sir_doc, ensure_ascii=False, separators=(',', ':'))
            else:
                result_content = json.dumps(sir_doc, ensure_ascii=False, indent=2)
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_content)]
            )
            
        except Exception as e:
            logger.error(f"SIR 转换失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"SIR 转换失败: {str(e)}")],
                isError=True
            )
    
    async def _convert_to_markdown(self, arguments: Dict[str, Any]) -> CallToolResult:
        """将 SIR 转换回 Markdown"""
        sir_content = arguments["sir_content"]
        output_format = arguments.get("output_format", "markdown")
        
        try:
            # 解析 SIR 内容
            sir_doc = json.loads(sir_content)
            
            # 转换为 Markdown
            markdown_content = render_sir_to_markdown(sir_doc)
            
            # 格式化输出
            if output_format == "pretty":
                result_content = json.dumps({
                    "markdown_content": markdown_content,
                    "length": len(markdown_content),
                    "line_count": markdown_content.count('\n') + 1
                }, ensure_ascii=False, indent=2)
            else:
                result_content = markdown_content
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_content)]
            )
            
        except Exception as e:
            logger.error(f"Markdown 转换失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Markdown 转换失败: {str(e)}")],
                isError=True
            )
    
    async def _semantic_edit(self, arguments: Dict[str, Any]) -> CallToolResult:
        """执行语义编辑操作"""
        file_path = arguments["file_path"]
        operation = arguments["operation"]
        parameters = arguments["parameters"]
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建编辑器
            editor = create_editor_from_markdown(content, file_path)
            
            # 执行编辑操作
            result = None
            
            if operation == "update_heading":
                result = editor.update_heading(
                    parameters.get("node_id"),
                    parameters.get("new_title"),
                    parameters.get("new_level")
                )
            elif operation == "insert_section":
                result = editor.insert_section(
                    parameters.get("parent_id"),
                    parameters.get("title"),
                    parameters.get("level"),
                    parameters.get("content"),
                    parameters.get("position", "after")
                )
            elif operation == "delete_section":
                result = editor.delete_section(parameters.get("node_id"))
            elif operation == "move_section":
                result = editor.move_section(
                    parameters.get("node_id"),
                    parameters.get("new_parent_id"),
                    parameters.get("position", "after")
                )
            elif operation == "update_content":
                result = editor.update_content(
                    parameters.get("node_id"),
                    parameters.get("new_content")
                )
            elif operation == "add_paragraph":
                result = editor.add_paragraph(
                    parameters.get("parent_id"),
                    parameters.get("content"),
                    parameters.get("position", "end")
                )
            elif operation == "add_code_block":
                result = editor.add_code_block(
                    parameters.get("parent_id"),
                    parameters.get("code"),
                    parameters.get("language"),
                    parameters.get("position", "end")
                )
            elif operation == "renumber_headings":
                result = editor.renumber_headings()
            elif operation == "fix_numbering":
                result = editor.fix_numbering()
            else:
                raise ValueError(f"不支持的编辑操作: {operation}")
            
            # 获取编辑后的文档
            edited_doc = editor.get_document()
            
            # 转换回 Markdown
            markdown_content = render_sir_to_markdown(edited_doc)
            
            # 保存结果（可选）
            if parameters.get("save_changes", False):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": True,
                    "operation": operation,
                    "result": result,
                    "edited_content": markdown_content,
                    "save_changes": parameters.get("save_changes", False)
                }, ensure_ascii=False, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"语义编辑失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"语义编辑失败: {str(e)}")],
                isError=True
            )
    
    async def _agent_edit_heading(self, arguments: Dict[str, Any]) -> CallToolResult:
        """智能体专用：更新标题内容和编号"""
        file_path = arguments["file_path"]
        node_id = arguments["node_id"]
        new_title = arguments["new_title"]
        new_level = arguments.get("new_level")
        auto_renumber = arguments.get("auto_renumber", True)
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建编辑器
            editor = create_editor_from_markdown(content, file_path)
            
            # 执行标题更新操作
            result = editor.update_heading(node_id, new_title, new_level)
            
            # 如果需要自动重新编号
            if auto_renumber:
                editor.renumber_headings()
            
            # 获取编辑后的文档
            edited_doc = editor.get_document()
            
            # 转换回 Markdown
            markdown_content = render_sir_to_markdown(edited_doc)
            
            # 保存结果
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": True,
                    "operation": "agent_edit_heading",
                    "node_id": node_id,
                    "new_title": new_title,
                    "new_level": new_level,
                    "auto_renumber": auto_renumber,
                    "edited_content": markdown_content,
                    "save_changes": True
                }, ensure_ascii=False, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"智能体标题编辑失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"智能体标题编辑失败: {str(e)}")],
                isError=True
            )
    
    async def _agent_renumber_headings(self, arguments: Dict[str, Any]) -> CallToolResult:
        """智能体专用：重新编号所有标题"""
        file_path = arguments["file_path"]
        numbering_style = arguments.get("numbering_style", "hierarchical")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建编辑器
            editor = create_editor_from_markdown(content, file_path)
            
            # 执行重新编号操作
            result = editor.renumber_headings()
            
            # 获取编辑后的文档
            edited_doc = editor.get_document()
            
            # 转换回 Markdown
            markdown_content = render_sir_to_markdown(edited_doc)
            
            # 保存结果
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": True,
                    "operation": "agent_renumber_headings",
                    "numbering_style": numbering_style,
                    "result": result,
                    "edited_content": markdown_content,
                    "save_changes": True
                }, ensure_ascii=False, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"智能体重编号失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"智能体重编号失败: {str(e)}")],
                isError=True
            )
    
    async def _agent_insert_section(self, arguments: Dict[str, Any]) -> CallToolResult:
        """智能体专用：插入新的章节"""
        file_path = arguments["file_path"]
        parent_id = arguments["parent_id"]
        title = arguments["title"]
        level = arguments.get("level", 2)
        content = arguments.get("content", "")
        position = arguments.get("position", "child")
        auto_renumber = arguments.get("auto_renumber", True)
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content_str = f.read()
            
            # 创建编辑器
            editor = create_editor_from_markdown(content_str, file_path)
            
            # 执行插入章节操作
            result = editor.insert_section(parent_id, title, level, content, position)
            
            # 如果需要自动重新编号
            if auto_renumber:
                editor.renumber_headings()
            
            # 获取编辑后的文档
            edited_doc = editor.get_document()
            
            # 转换回 Markdown
            markdown_content = render_sir_to_markdown(edited_doc)
            
            # 保存结果
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": True,
                    "operation": "agent_insert_section",
                    "parent_id": parent_id,
                    "title": title,
                    "level": level,
                    "content": content,
                    "position": position,
                    "auto_renumber": auto_renumber,
                    "result": result,
                    "edited_content": markdown_content,
                    "save_changes": True
                }, ensure_ascii=False, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"智能体插入章节失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"智能体插入章节失败: {str(e)}")],
                isError=True
            )
    
    async def _agent_check_numbering(self, arguments: Dict[str, Any]) -> CallToolResult:
        """智能体专用：检查标题编号一致性"""
        file_path = arguments["file_path"]
        check_types = arguments.get("check_types", ["duplicates", "discontinuous"])
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建编辑器
            editor = create_editor_from_markdown(content, file_path)
            
            # 执行编号检查
            numbering_result = editor.check_numbering_consistency()
            
            # 过滤检查结果
            filtered_result = {}
            if "duplicates" in check_types:
                filtered_result["duplicates"] = numbering_result.get("duplicates", [])
            if "discontinuity" in check_types:
                filtered_result["discontinuity"] = numbering_result.get("discontinuous", [])
            if "format" in check_types:
                filtered_result["format"] = numbering_result.get("format_issues", [])
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": True,
                    "operation": "agent_check_numbering",
                    "file_path": file_path,
                    "check_types": check_types,
                    "issues": filtered_result,
                    "has_issues": any(len(issues) > 0 for issues in filtered_result.values())
                }, ensure_ascii=False, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"智能体编号检查失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"智能体编号检查失败: {str(e)}")],
                isError=True
            )
    
    async def _analyze_document(self, arguments: Dict[str, Any]) -> CallToolResult:
        """分析文档结构"""
        file_path = arguments["file_path"]
        check_types = arguments.get("check_types", ["structure", "numbering", "consistency"])
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建编辑器
            editor = create_editor_from_markdown(content, file_path)
            
            # 执行分析
            analysis_result = {
                "file_path": file_path,
                "analysis": {}
            }
            
            if "structure" in check_types:
                analysis_result["analysis"]["structure"] = editor.check_structure()
            
            if "numbering" in check_types:
                analysis_result["analysis"]["numbering"] = editor.check_numbering_consistency()
            
            if "consistency" in check_types:
                analysis_result["analysis"]["consistency"] = editor.check_consistency()
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(
                    analysis_result, ensure_ascii=False, indent=2
                ))]
            )
            
        except Exception as e:
            logger.error(f"文档分析失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"文档分析失败: {str(e)}")],
                isError=True
            )
    
    async def _format_markdown(self, arguments: Dict[str, Any]) -> CallToolResult:
        """格式化 Markdown 文档"""
        file_path = arguments["file_path"]
        style = arguments.get("style", "github")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 通过 SIR 进行格式化和清理
            from markdown_editor.sir_renderer import RenderStyle
            
            render_style = RenderStyle.GITHUB
            if style == "standard":
                render_style = RenderStyle.STANDARD
            elif style == "compact":
                render_style = RenderStyle.COMPACT
            
            # 转换到 SIR 再转回 Markdown 以实现格式化
            formatted_content = render_sir_to_markdown(
                convert_markdown_to_sir(content, file_path),
                style=render_style
            )
            
            # 保存格式化后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "success": True,
                    "file_path": file_path,
                    "original_length": len(content),
                    "formatted_length": len(formatted_content),
                    "line_count": formatted_content.count('\n') + 1,
                    "style": style
                }, ensure_ascii=False, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"文档格式化失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"文档格式化失败: {str(e)}")],
                isError=True
            )
    
    async def run(self):
        """运行 MCP 服务器"""
        logger.info("启动 Markdown Editor MCP 服务器...")
        logger.info("等待客户端连接...")
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("客户端已连接，开始处理请求")
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"服务器运行时发生错误: {e}", exc_info=True)
            raise
        finally:
            logger.info("服务器连接已断开")


async def main():
    """主函数"""
    server = MarkdownEditorMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        sys.exit(1)