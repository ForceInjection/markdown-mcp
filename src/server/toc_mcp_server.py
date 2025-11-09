#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown TOC MCP Server

专门为 Markdown 文档目录处理设计的 MCP 服务器，
提供三大核心功能：

1. extract_markdown_toc - 提取 Markdown 文档的目录结构
2. analyze_numbering_issues - 分析 Markdown 文档中的编号问题（重复、不连续等）
3. generate_toc - 生成格式化的 TOC 内容
"""

import asyncio
import json
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from markdown_toc.extractor import MarkdownTOCExtractor

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
    log_file = log_dir / "toc_mcp_server.log"
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


class MCPServer:
    """Markdown TOC MCP 服务器主类"""
    
    def __init__(self):
        """初始化 MCP 服务器"""
        logger.info("正在初始化 Markdown TOC MCP 服务器...")
        self.server = Server("markdown-toc-mcp-server")
        self.setup_handlers()
        logger.info("MCP 服务器初始化完成")
        
    def setup_handlers(self):
        """设置请求处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用工具列表"""
            return [
                Tool(
                    name="extract_markdown_toc",
                    description="提取 Markdown 文档的目录结构",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径"
                            },
                            "output_format": {
                                "type": "string",
                                "description": "输出格式",
                                "enum": ["json", "text", "markdown"],
                                "default": "json"
                            },
                            "min_depth": {
                                "type": "integer",
                                "description": "最小标题深度",
                                "default": 1,
                                "minimum": 1,
                                "maximum": 6
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "最大标题深度",
                                "default": 6,
                                "minimum": 1,
                                "maximum": 6
                            },
                            "include_line_numbers": {
                                "type": "boolean",
                                "description": "是否包含行号信息",
                                "default": False
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="analyze_numbering_issues",
                    description="分析 Markdown 文档中的编号问题（重复、不连续等）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径"
                            },
                            "check_types": {
                                "type": "array",
                                "description": "要检查的问题类型",
                                "items": {
                                    "type": "string",
                                    "enum": ["duplicates", "discontinuous"]
                                },
                                "default": ["duplicates", "discontinuous"]
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="generate_toc",
                    description="生成格式化的 TOC 内容供插入文档",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Markdown 文件路径"
                            },
                            "format_type": {
                                "type": "string",
                                "description": "输出格式",
                                "enum": ["markdown", "html", "text"],
                                "default": "markdown"
                            },
                            "include_links": {
                                "type": "boolean",
                                "description": "是否包含链接（仅对 markdown 格式有效）",
                                "default": True
                            },
                            "max_level": {
                                "type": "integer",
                                "description": "最大包含的标题级别",
                                "minimum": 1,
                                "maximum": 6,
                                "default": 6
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
                if name == "extract_markdown_toc":
                    result = await self._extract_markdown_toc(arguments)
                    logger.info(f"TOC 提取完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "analyze_numbering_issues":
                    result = await self._analyze_numbering_issues(arguments)
                    logger.info(f"编号分析完成: {arguments.get('file_path', 'unknown')}")
                    return result
                elif name == "generate_toc":
                    result = await self._generate_toc(arguments)
                    logger.info(f"TOC 生成完成: {arguments.get('file_path', 'unknown')}")
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
    
    async def _extract_markdown_toc(self, arguments: Dict[str, Any]) -> CallToolResult:
        """提取 Markdown 文档的目录结构"""
        file_path = arguments["file_path"]
        output_format = arguments.get("output_format", "json")
        min_depth = arguments.get("min_depth", 1)
        max_depth = arguments.get("max_depth", 6)
        include_line_numbers = arguments.get("include_line_numbers", False)
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用核心提取器
            extractor = MarkdownTOCExtractor()
            headers = extractor.extract_toc(
                content, 
                min_depth=min_depth, 
                max_depth=max_depth, 
                include_line_numbers=include_line_numbers
            )
            
            # 格式化输出
            if output_format == "json":
                result_content = json.dumps(headers, ensure_ascii=False, indent=2)
            elif output_format == "text":
                result_content = self._format_toc_as_text(headers, file_path)
            elif output_format == "markdown":
                result_content = self._format_toc_as_markdown(headers, file_path)
            else:
                result_content = json.dumps(headers, ensure_ascii=False, indent=2)
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_content)]
            )
            
        except Exception as e:
            logger.error(f"TOC 提取失败: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"TOC 提取失败: {str(e)}")],
                isError=True
            )
    
    async def _analyze_numbering_issues(self, arguments: Dict[str, Any]) -> CallToolResult:
        """分析 Markdown 文档中的编号问题"""
        file_path = arguments["file_path"]
        check_types = arguments.get("check_types", ["duplicates", "discontinuous"])
        
        try:
            # 验证文件路径
            if not file_path:
                raise ValueError("文件路径不能为空")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 检查是否为文件（而非目录）
            if not os.path.isfile(file_path):
                raise ValueError(f"路径不是文件: {file_path}")
            
            logger.info(f"开始分析文件编号问题: {file_path}")
            
            # 读取文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 尝试其他编码
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                logger.warning(f"文件使用 GBK 编码: {file_path}")
            
            if not content.strip():
                logger.warning(f"文件内容为空: {file_path}")
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps({
                        "file_path": file_path,
                        "total_headers": 0,
                        "issues": {
                            "has_issues": False,
                            "duplicate_numbers": [],
                            "discontinuous_numbers": [],
                            "statistics": {
                                "total_headers": 0,
                                "numbered_headers": 0,
                                "levels_with_issues": 0
                            }
                        },
                        "has_issues": False
                    }, ensure_ascii=False, indent=2))]
                )
            
            # 使用核心提取器
            extractor = MarkdownTOCExtractor()
            headers = extractor.extract_toc(content)
            logger.debug(f"提取到 {len(headers)} 个标题")
            
            issues = extractor.analyze_numbering_issues(headers, check_types=check_types)
            logger.debug(f"编号分析完成，发现问题: {issues.get('has_issues', False)}")
            
            result = {
                "file_path": file_path,
                "total_headers": len(headers),
                "issues": issues,
                "has_issues": issues.get("has_issues", False)
            }
            
            logger.info(f"编号分析完成: {file_path}, 总标题数: {len(headers)}, 存在问题: {issues.get('has_issues', False)}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            )
            
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"文件未找到: {str(e)}")],
                isError=True
            )
        except ValueError as e:
            logger.error(f"参数错误: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"参数错误: {str(e)}")],
                isError=True
            )
        except UnicodeDecodeError as e:
            logger.error(f"文件编码错误: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"文件编码错误，请确保文件为 UTF-8 或 GBK 编码: {str(e)}")],
                isError=True
            )
        except Exception as e:
            logger.error(f"编号分析失败: {e}", exc_info=True)
            return CallToolResult(
                content=[TextContent(type="text", text=f"编号分析失败: {str(e)}")],
                isError=True
            )
    
    async def _generate_toc(self, arguments: Dict[str, Any]) -> CallToolResult:
        """生成格式化的 TOC 内容"""
        file_path = arguments["file_path"]
        format_type = arguments.get("format_type", "markdown")
        include_links = arguments.get("include_links", True)
        max_level = arguments.get("max_level")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用核心提取器
            extractor = MarkdownTOCExtractor()
            headers = extractor.extract_toc(content)
            
            # 生成 TOC
            toc_result = extractor.generate_toc(
                headers, 
                format_type=format_type, 
                include_links=include_links,
                max_level=max_level
            )
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "file_path": file_path,
                            "toc_content": toc_result['content'],
                            "format": toc_result['format'],
                            "stats": {
                                "total_items": toc_result['total_items'],
                                "levels_included": toc_result['levels_included'],
                                "format_used": toc_result['format']
                            },
                            "parameters": {
                                "format_type": format_type,
                                "include_links": include_links,
                                "max_level": max_level
                            }
                        }, ensure_ascii=False, indent=2)
                    )
                ]
            )
            
        except Exception as e:
            logger.error(f"TOC 生成失败: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"TOC 生成失败: {str(e)}",
                            "file_path": file_path
                        }, ensure_ascii=False, indent=2)
                    )
                ],
                isError=True
            )
        
    
    def _format_toc_as_text(self, headers: List[Dict], file_path: str) -> str:
        """将 TOC 格式化为文本"""
        lines = [f"目录结构 - {file_path}", "=" * 50]
        
        for header in headers:
            indent = "  " * (header['level'] - 1)
            lines.append(f"{indent}{header['level']}. {header['title']} (行 {header['line_number']})")
        
        return "\n".join(lines)
    
    def _format_toc_as_markdown(self, headers: List[Dict], file_path: str) -> str:
        """将 TOC 格式化为 Markdown"""
        lines = [f"# 目录 - {Path(file_path).name}", ""]
        
        for header in headers:
            indent = "  " * (header['level'] - 1)
            lines.append(f"{indent}- {header['title']}")
        
        return "\n".join(lines)
    
    async def run(self):
        """运行 MCP 服务器"""
        logger.info("启动 Markdown TOC MCP 服务器...")
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
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        sys.exit(1)