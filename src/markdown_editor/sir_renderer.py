"""
SIR 到 Markdown 反向渲染器

将 SIR (Structured Intermediate Representation) 转换回 Markdown 格式，
支持完整的双向转换能力。

遵循文章《智能体如何高效处理 Markdown：结构化解析与语义编辑方案》的设计理念。
"""

from typing import Dict, List, Optional, Any, Union
import re
from enum import Enum

from .sir_schema import (
    SIRDocument, SIRNode, NodeType, HeadingLevel, HeadingNode, ParagraphNode,
    CodeBlockNode, ListNode, ListItemNode, TableNode, TableCellNode, SIRConfig
)
from .source_map import SourceMap, MappingType


class RenderStyle(str, Enum):
    """渲染风格枚举"""
    COMMONMARK = "commonmark"      # 严格的 CommonMark 规范
    GITHUB = "github"              # GitHub Flavored Markdown
    EXTENDED = "extended"          # 扩展 Markdown (表格、任务列表等)
    COMPACT = "compact"            # 紧凑格式
    PRETTY = "pretty"             # 美化格式


class SIRRenderer:
    """SIR 到 Markdown 渲染器"""
    
    def __init__(self, config: Optional[SIRConfig] = None, 
                 style: RenderStyle = RenderStyle.GITHUB):
        self.config = config or SIRConfig()
        self.style = style
        self.indent_level = 0
        self.current_heading_levels = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    
    def render(self, sir_document: SIRDocument) -> str:
        """将 SIR 文档渲染为 Markdown"""
        try:
            self._reset_state()
            
            # 渲染文档元数据（如果有）
            metadata_lines = self._render_metadata(sir_document.get("metadata", {}))
            
            # 渲染 AST 内容
            content_lines = self._render_node(sir_document["ast"])
            
            # 合并结果
            result_lines = []
            if metadata_lines:
                result_lines.extend(metadata_lines)
                result_lines.append("\n")  # 元数据和内容之间的空行
            
            result_lines.extend(content_lines)
            
            return "\n".join(result_lines).strip() + "\n"
            
        except Exception as e:
            raise ValueError(f"Failed to render SIR to Markdown: {e}")
    
    def _render_node(self, node: SIRNode) -> List[str]:
        """渲染单个节点"""
        node_type = node["type"]
        
        if node_type == NodeType.DOCUMENT:
            return self._render_root(node)
        elif node_type == NodeType.HEADING:
            return self._render_heading(node)
        elif node_type == NodeType.PARAGRAPH:
            return self._render_paragraph(node)
        elif node_type == NodeType.CODE_BLOCK:
            return self._render_code_block(node)
        elif node_type == NodeType.LIST:
            return self._render_list(node)
        elif node_type == NodeType.LIST_ITEM:
            return self._render_list_item(node)
        elif node_type == NodeType.TABLE:
            return self._render_table(node)
        elif node_type == NodeType.TABLE_CELL:
            return self._render_table_cell(node)
        elif node_type == NodeType.BLOCKQUOTE:
            return self._render_blockquote(node)
        elif node_type == NodeType.HR:
            return self._render_horizontal_rule()
        elif node_type == NodeType.HTML_BLOCK:
            return self._render_html_block(node)
        else:
            # 未知节点类型，尝试渲染内容
            content = node.get("content", "")
            if content:
                return [content]
            return []
    
    def _render_root(self, node: SIRNode) -> List[str]:
        """渲染根节点"""
        result = []
        for child in node.get("children", []):
            child_lines = self._render_node(child)
            if child_lines:
                result.extend(child_lines)
                # 在块级元素之间添加空行
                if self._is_block_element(child):
                    result.append("")
        
        # 移除末尾多余的空行
        while result and result[-1] == "":
            result.pop()
            
        return result
    
    def _render_heading(self, node: HeadingNode) -> List[str]:
        """渲染标题"""
        level = node.get("level", 1)
        title = node.get("title", "") or node.get("content", "")
        children = node.get("children", [])
        
        # 如果没有直接内容，检查子节点中的内容
        if not title and children:
            # 从子节点中提取内容
            title_parts = []
            for child in children:
                if child.get("type") == NodeType.INLINE and child.get("content"):
                    title_parts.append(child["content"])
                elif child.get("type") == NodeType.PARAGRAPH and child.get("content"):
                    title_parts.append(child["content"])
                elif child.get("content"):
                    title_parts.append(child["content"])
            
            if title_parts:
                title = " ".join(title_parts)
        
        if not title:
            return []
        
        # 更新当前标题级别计数
        self._update_heading_levels(level)
        
        # 根据风格选择渲染方式
        if self.style in [RenderStyle.COMMONMARK, RenderStyle.GITHUB]:
            # 使用 # 语法
            prefix = "#" * level
            
            # 添加自动编号（如果启用）
            auto_number = node.get("auto_number")
            if auto_number and self.config.auto_number_headings:
                heading_line = f"{prefix} {auto_number} {title}"
            else:
                heading_line = f"{prefix} {title}"
        else:
            # 使用下划线语法（仅支持1-2级）
            if level == 1:
                heading_line = title
                underline = "=" * len(title)
            elif level == 2:
                heading_line = title
                underline = "-" * len(title)
            else:
                prefix = "#" * level
                heading_line = f"{prefix} {title}"
        
        result = []
        if level in [1, 2] and self.style not in [RenderStyle.COMMONMARK, RenderStyle.GITHUB]:
            result.append(heading_line)
            result.append(underline)
        else:
            result.append(heading_line)
        
        # 渲染子节点内容（段落和子标题）
        for child in children:
            if child["type"] == NodeType.PARAGRAPH:
                # 渲染段落子节点
                para_lines = self._render_paragraph(child)
                result.extend(para_lines)
            elif child["type"] == NodeType.HEADING:
                # 递归渲染子标题
                heading_lines = self._render_heading(child)
                result.extend(heading_lines)
        
        return result
    
    def _render_paragraph(self, node: ParagraphNode) -> List[str]:
        """渲染段落"""
        content = node.get("content", "")
        
        # 如果没有直接内容，检查子节点中的内容
        if not content and node.get("children"):
            # 从子节点中提取内容
            content_parts = []
            for child in node["children"]:
                if child.get("type") == NodeType.INLINE and child.get("content"):
                    content_parts.append(child["content"])
                elif child.get("content"):
                    content_parts.append(child["content"])
            
            if content_parts:
                content = " ".join(content_parts)
        
        if not content:
            return []
        
        # 处理内联格式
        content = self._render_inline_formatting(content)
        
        return [content]
    
    def _render_code_block(self, node: CodeBlockNode) -> List[str]:
        """渲染代码块"""
        content = node.get("content", "")
        language = node.get("language", "")
        
        if not content:
            return []
        
        lines = content.split('\n')
        
        # 添加代码块标记
        result = []
        if language:
            result.append(f"```{language}")
        else:
            result.append("```")
        
        result.extend(lines)
        result.append("```")
        
        return result
    
    def _render_list(self, node: ListNode) -> List[str]:
        """渲染列表"""
        list_type = node.get("list_type", "unordered")
        items = node.get("children", [])
        
        if not items:
            return []
        
        result = []
        
        for i, item in enumerate(items):
            if item["type"] == NodeType.LIST_ITEM:
                item_lines = self._render_list_item(item, list_type, i + 1)
                result.extend(item_lines)
        
        return result
    
    def _render_list_item(self, node: ListItemNode, 
                         list_type: str = "unordered", 
                         index: int = 1) -> List[str]:
        """渲染列表项"""
        content = node.get("content", "")
        children = node.get("children", [])
        
        # 如果没有直接内容，检查子节点中的内容
        if not content and children:
            # 从子节点中提取内容
            content_parts = []
            for child in children:
                if child.get("type") == NodeType.INLINE and child.get("content"):
                    content_parts.append(child["content"])
                elif child.get("content"):
                    content_parts.append(child["content"])
            
            if content_parts:
                content = " ".join(content_parts)
        
        # 确定前缀
        if list_type == "ordered":
            prefix = f"{index}."
        elif list_type == "task":
            checked = node.get("checked", False)
            prefix = f"- [{'x' if checked else ' '}]"
        else:
            prefix = "-"
        
        # 渲染内容
        lines = []
        if content:
            content = self._render_inline_formatting(content)
            lines.append(f"{prefix} {content}")
        else:
            lines.append(prefix)
        
        # 渲染子内容（嵌套列表或段落）
        for child in children:
            if child["type"] == NodeType.LIST:
                # 嵌套列表
                nested_lines = self._render_list(child)
                for nested_line in nested_lines:
                    lines.append(f"  {nested_line}")
            elif child["type"] == NodeType.PARAGRAPH:
                # 列表项中的段落
                para_lines = self._render_paragraph(child)
                for para_line in para_lines:
                    lines.append(f"  {para_line}")
        
        return lines
    
    def _render_table(self, node: TableNode) -> List[str]:
        """渲染表格"""
        if self.style not in [RenderStyle.GITHUB, RenderStyle.EXTENDED]:
            # 不支持表格的格式，返回空
            return []
        
        rows = node.get("children", [])
        if not rows:
            return []
        
        result = []
        
        # 处理表头
        header_row = None
        data_rows = []
        
        for row in rows:
            if row.get("is_header", False):
                header_row = row
            else:
                data_rows.append(row)
        
        # 渲染表头
        if header_row:
            header_cells = self._render_table_row(header_row, is_header=True)
            result.append(header_cells)
            
            # 添加分隔行
            separator = "| " + " | ".join(["---"] * len(header_row.get("children", []))) + " |"
            result.append(separator)
        
        # 渲染数据行
        for row in data_rows:
            row_line = self._render_table_row(row, is_header=False)
            result.append(row_line)
        
        return result
    
    def _render_table_row(self, row: SIRNode, is_header: bool = False) -> str:
        """渲染表格行"""
        cells = row.get("children", [])
        cell_contents = []
        
        for cell in cells:
            content = cell.get("content", "")
            # 清理内容中的管道符
            content = content.replace("|", "&#124;")
            cell_contents.append(content)
        
        return "| " + " | ".join(cell_contents) + " |"
    
    def _render_table_cell(self, node: TableCellNode) -> List[str]:
        """渲染表格单元格"""
        # 表格单元格通常在表格行中处理
        content = node.get("content", "")
        
        # 如果没有直接内容，检查子节点中的内容
        if not content and node.get("children"):
            # 从子节点中提取内容
            content_parts = []
            for child in node["children"]:
                if child.get("type") == NodeType.INLINE and child.get("content"):
                    content_parts.append(child["content"])
                elif child.get("content"):
                    content_parts.append(child["content"])
            
            if content_parts:
                content = " ".join(content_parts)
        
        return [content]
    
    def _render_blockquote(self, node: SIRNode) -> List[str]:
        """渲染引用块"""
        content = node.get("content", "")
        if not content:
            return []
        
        lines = content.split('\n')
        quoted_lines = [f"> {line}" for line in lines]
        return quoted_lines
    
    def _render_horizontal_rule(self) -> List[str]:
        """渲染水平分割线"""
        if self.style == RenderStyle.COMMONMARK:
            return ["---"]
        else:
            return ["***"]
    
    def _render_html_block(self, node: SIRNode) -> List[str]:
        """渲染 HTML 块"""
        content = node.get("content", "")
        return [content]
    
    def _render_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """渲染文档元数据"""
        if not metadata:
            return []
        
        result = []
        
        # YAML front matter 格式
        if self.style in [RenderStyle.GITHUB, RenderStyle.EXTENDED]:
            result.append("---")
            for key, value in metadata.items():
                if isinstance(value, list):
                    result.append(f"{key}:")
                    for item in value:
                        result.append(f"  - {item}")
                elif isinstance(value, dict):
                    result.append(f"{key}:")
                    for sub_key, sub_value in value.items():
                        result.append(f"  {sub_key}: {sub_value}")
                else:
                    result.append(f"{key}: {value}")
            result.append("---")
        
        return result
    
    def _render_inline_formatting(self, text: str) -> str:
        """渲染内联格式"""
        # 这里主要处理文本内容中的特殊字符转义
        # 在实际实现中，应该基于 SIR 中的内联节点信息进行渲染
        
        # 转义特殊字符
        text = text.replace("*", "\\*")
        text = text.replace("_", "\\_")
        text = text.replace("`", "\\`")
        text = text.replace("#", "\\#")
        text = text.replace("+", "\\+")
        text = text.replace("-", "\\-")
        text = text.replace(".", "\\.")
        text = text.replace("!", "\\!")
        
        return text
    
    def _update_heading_levels(self, level: int):
        """更新标题级别计数"""
        if 1 <= level <= 6:
            # 重置更低级别的计数
            for l in range(level + 1, 7):
                self.current_heading_levels[l] = 0
            
            # 递增当前级别计数
            self.current_heading_levels[level] += 1
    
    def _is_block_element(self, node: SIRNode) -> bool:
        """判断是否为块级元素"""
        block_types = [
            NodeType.HEADING, NodeType.PARAGRAPH, NodeType.CODE_BLOCK,
            NodeType.LIST, NodeType.TABLE, NodeType.BLOCKQUOTE,
            NodeType.HR, NodeType.HTML_BLOCK
        ]
        return node["type"] in block_types
    
    def _reset_state(self):
        """重置渲染状态"""
        self.indent_level = 0
        self.current_heading_levels = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}


def create_sir_renderer(config: Optional[SIRConfig] = None, 
                       style: RenderStyle = RenderStyle.GITHUB) -> SIRRenderer:
    """创建 SIR 渲染器实例"""
    return SIRRenderer(config, style)


def render_sir_to_markdown(sir_document: SIRDocument, 
                          config: Optional[SIRConfig] = None,
                          style: RenderStyle = RenderStyle.GITHUB) -> str:
    """将 SIR 文档渲染为 Markdown"""
    renderer = SIRRenderer(config, style)
    return renderer.render(sir_document)


def convert_markdown_to_markdown(markdown_content: str, 
                                source_file: Optional[str] = None,
                                config: Optional[SIRConfig] = None,
                                style: RenderStyle = RenderStyle.GITHUB) -> str:
    """
    Markdown 到 Markdown 的转换（通过 SIR 中间层）
    可用于格式化和清理 Markdown 文档
    """
    from .sir_converter import convert_markdown_to_sir
    
    # 转换为 SIR
    sir_doc = convert_markdown_to_sir(markdown_content, source_file)
    
    # 渲染回 Markdown
    return render_sir_to_markdown(sir_doc, config, style)