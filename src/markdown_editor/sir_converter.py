"""
AST 到 SIR 转换器

将 markdown-it-py 生成的 AST 转换为 SIR (Structured Intermediate Representation)
遵循文章《智能体如何高效处理 Markdown：结构化解析与语义编辑方案》的设计理念。
"""

import re
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

from .ast_parser import ASTNode, ASTNodeType, MarkdownASTParser
from .sir_schema import (
    SIRConfig, SIRDocument, SIRNode, SIRMetadata, SourcePosition, 
    SourceLocation, NodeType, HeadingLevel, HeadingNode, ParagraphNode,
    CodeBlockNode, ListNode, ListItemNode, TableNode, TableRowNode,
    TableCellNode, BlockquoteNode, create_sir_metadata
)
from .source_map import SourceMap, MappingType


class SIRConverter:
    """AST 到 SIR 转换器"""
    
    def __init__(self, config: Optional[SIRConfig] = None):
        self.config = config or SIRConfig()
        self.source_map: Optional[SourceMap] = None
        self.node_counter = 0
        self.current_document: Optional[SIRDocument] = None
        self.original_content: Optional[str] = None
        self.current_heading_levels = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    
    def convert(self, ast_node: ASTNode, source_file: Optional[str] = None, 
                original_content: Optional[str] = None) -> SIRDocument:
        """将 AST 转换为 SIR 文档"""
        # 初始化文档和Source Map
        metadata = create_sir_metadata(source_file)
        self.source_map = SourceMap(original_content=original_content, source_file=source_file)
        self.original_content = original_content
        
        # 重置标题级别计数器
        self.current_heading_levels = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        # 转换根节点
        sir_root = self._convert_node(ast_node, None)
        
        # 构建完整文档
        self.current_document = {
            "metadata": metadata,
            "ast": sir_root,
            "source_map": self.source_map.to_dict(),
            "errors": [],
            "warnings": []
        }
        
        # 更新统计信息
        self._update_statistics(metadata, sir_root)
        
        return self.current_document
    
    def _convert_node(self, ast_node: ASTNode, parent_id: Optional[str]) -> SIRNode:
        """转换单个 AST 节点到 SIR 节点"""
        node_id = self._generate_node_id()
        
        # 根据节点类型进行转换
        sir_node: Optional[SIRNode] = None
        
        if ast_node.type == ASTNodeType.ROOT:
            sir_node = self._convert_root_node(ast_node, node_id)
        elif ast_node.type == ASTNodeType.HEADING:
            sir_node = self._convert_heading_node(ast_node, node_id)
        elif ast_node.type in [ASTNodeType.PARAGRAPH, ASTNodeType.TEXT]:
            sir_node = self._convert_paragraph_node(ast_node, node_id)
        elif ast_node.type in [ASTNodeType.CODE_BLOCK, ASTNodeType.FENCED_CODE]:
            sir_node = self._convert_code_block_node(ast_node, node_id)
        elif ast_node.type == ASTNodeType.LIST:
            sir_node = self._convert_list_node(ast_node, node_id)
        elif ast_node.type == ASTNodeType.LIST_ITEM:
            sir_node = self._convert_list_item_node(ast_node, node_id)
        elif ast_node.type == ASTNodeType.TABLE:
            sir_node = self._convert_table_node(ast_node, node_id)
        elif ast_node.type == ASTNodeType.TABLE_ROW:
            sir_node = self._convert_table_row_node(ast_node, node_id)
        elif ast_node.type == ASTNodeType.TABLE_CELL:
            sir_node = self._convert_table_cell_node(ast_node, node_id)
        elif ast_node.type == ASTNodeType.BLOCKQUOTE:
            sir_node = self._convert_blockquote_node(ast_node, node_id)
        else:
            # 默认处理为通用节点
            sir_node = self._convert_generic_node(ast_node, node_id)
        
        # 设置父节点ID
        if sir_node:
            sir_node["parent_id"] = parent_id
        
        # 递归处理子节点
        if sir_node and ast_node.children:
            sir_node["children"] = []
            for child_ast in ast_node.children:
                child_sir = self._convert_node(child_ast, node_id)
                sir_node["children"].append(child_sir)
        
        # 记录源代码位置到Source Map
        if sir_node and self.config.preserve_source_locations and ast_node.source_pos:
            source_location = self._convert_source_position(ast_node.source_pos)
            sir_node["source_location"] = source_location
            
            # 获取原始文本内容
            original_text = None
            if self.original_content and ast_node.source_pos:
                start_line, start_col = ast_node.source_pos[0]
                end_line, end_col = ast_node.source_pos[1]
                original_text = self._extract_original_text(start_line, start_col, end_line, end_col)
            
            # 添加到Source Map
            if sir_node and source_location:
                self.source_map.add_mapping(
                    sir_node=sir_node,
                    original_text=original_text or "",
                    start_line=source_location["start"]["line"],
                    start_col=source_location["start"]["column"],
                    end_line=source_location["end"]["line"],
                    end_col=source_location["end"]["column"],
                    mapping_type=MappingType.EXACT if original_text else MappingType.APPROXIMATE
                )
        
        return sir_node or self._create_fallback_node(ast_node, node_id, parent_id)
    
    def _convert_root_node(self, ast_node: ASTNode, node_id: str) -> SIRNode:
        """转换根节点"""
        return {
            "id": node_id,
            "type": NodeType.DOCUMENT,
            "content": None,
            "children": [],
            "attributes": {"node_type": "document"},
            "source_location": None,
            "parent_id": None
        }
    
    def _convert_heading_node(self, ast_node: ASTNode, node_id: str) -> HeadingNode:
        """转换标题节点"""
        level = ast_node.attrs.get("level", 1)
        title = ast_node.content or ""
        
        # 清理标题文本
        clean_title = self._clean_title_text(title)
        
        # 生成锚点
        anchor = self._generate_anchor(clean_title) if self.config.generate_anchors else None
        
        # 自动编号
        auto_number = self._generate_auto_number(level) if self.config.auto_number_headings else None
        
        return {
            "id": node_id,
            "type": NodeType.HEADING,
            "content": clean_title,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None,
            "level": HeadingLevel(level),
            "title": clean_title,
            "anchor": anchor,
            "auto_number": auto_number
        }
    
    def _convert_paragraph_node(self, ast_node: ASTNode, node_id: str) -> ParagraphNode:
        """转换段落节点"""
        content = ast_node.content or ""
        
        return {
            "id": node_id,
            "type": NodeType.PARAGRAPH,
            "content": content,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None
        }
    
    def _convert_code_block_node(self, ast_node: ASTNode, node_id: str) -> CodeBlockNode:
        """转换代码块节点"""
        language = ast_node.attrs.get("language")
        content = ast_node.content or ""
        
        return {
            "id": node_id,
            "type": NodeType.CODE_BLOCK,
            "content": content,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None,
            "language": language,
            "info": language
        }
    
    def _convert_list_node(self, ast_node: ASTNode, node_id: str) -> ListNode:
        """转换列表节点"""
        ordered = ast_node.attrs.get("ordered", False)
        start = ast_node.attrs.get("start")
        tight = ast_node.attrs.get("tight", False)
        
        return {
            "id": node_id,
            "type": NodeType.LIST,
            "content": None,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None,
            "ordered": ordered,
            "start": start,
            "tight": tight
        }
    
    def _convert_list_item_node(self, ast_node: ASTNode, node_id: str) -> ListItemNode:
        """转换列表项节点"""
        checked = ast_node.attrs.get("checked")
        spread = ast_node.attrs.get("spread", False)
        
        return {
            "id": node_id,
            "type": NodeType.LIST_ITEM,
            "content": ast_node.content,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None,
            "checked": checked,
            "spread": spread
        }
    
    def _convert_table_node(self, ast_node: ASTNode, node_id: str) -> TableNode:
        """转换表格节点"""
        align = ast_node.attrs.get("align", [])
        header = ast_node.attrs.get("header", False)
        
        return {
            "id": node_id,
            "type": NodeType.TABLE,
            "content": None,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None,
            "header": header,
            "align": align
        }
    
    def _convert_table_row_node(self, ast_node: ASTNode, node_id: str) -> TableRowNode:
        """转换表格行节点"""
        is_header = ast_node.attrs.get("is_header", False)
        
        return {
            "id": node_id,
            "type": NodeType.TABLE_ROW,
            "content": None,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None,
            "is_header": is_header
        }
    
    def _convert_table_cell_node(self, ast_node: ASTNode, node_id: str) -> TableCellNode:
        """转换表格单元格节点"""
        return {
            "id": node_id,
            "type": NodeType.TABLE_CELL,
            "content": ast_node.content,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None
        }
    
    def _convert_blockquote_node(self, ast_node: ASTNode, node_id: str) -> BlockquoteNode:
        """转换引用块节点"""
        return {
            "id": node_id,
            "type": NodeType.BLOCKQUOTE,
            "content": ast_node.content,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None
        }
    
    def _convert_generic_node(self, ast_node: ASTNode, node_id: str) -> SIRNode:
        """转换通用节点"""
        return {
            "id": node_id,
            "type": NodeType.INLINE,
            "content": ast_node.content,
            "children": [],
            "attributes": ast_node.attrs,
            "source_location": None,
            "parent_id": None
        }
    
    def _create_fallback_node(self, ast_node: ASTNode, node_id: str, parent_id: Optional[str]) -> SIRNode:
        """创建回退节点"""
        return {
            "id": node_id,
            "type": NodeType.INLINE,
            "content": ast_node.content or "",
            "children": [],
            "attributes": ast_node.attrs or {},
            "source_location": None,
            "parent_id": parent_id
        }
    
    def _convert_source_position(self, source_pos: Tuple[Tuple[int, int], Tuple[int, int]]) -> SourceLocation:
        """转换源代码位置信息"""
        start_line, start_col = source_pos[0]
        end_line, end_col = source_pos[1]
        
        return {
            "start": {"line": start_line, "column": start_col, "offset": 0},
            "end": {"line": end_line, "column": end_col, "offset": 0},
            "filename": None
        }
    
    def _clean_title_text(self, title: str) -> str:
        """清理标题文本"""
        # 移除Markdown格式
        clean_title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)  # 粗体
        clean_title = re.sub(r'\*(.*?)\*', r'\1', clean_title)    # 斜体
        clean_title = re.sub(r'`(.*?)`', r'\1', clean_title)      # 代码
        clean_title = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', clean_title)  # 链接
        
        # 移除首尾空格
        clean_title = clean_title.strip()
        
        return clean_title
    
    def _generate_anchor(self, title: str) -> str:
        """生成URL友好的锚点"""
        # 转换为小写
        anchor = title.lower()
        
        # 替换非字母数字字符为连字符
        anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
        
        # 替换空格为连字符
        anchor = re.sub(r'[\s-]+', '-', anchor)
        
        # 移除首尾连字符
        anchor = anchor.strip('-')
        
        return anchor
    
    def _generate_auto_number(self, level: int) -> str:
        """生成自动编号"""
        # 基于当前标题级别计数生成正确的多级编号
        self.current_heading_levels[level] += 1
        
        # 重置更低级别的计数器
        for l in range(level + 1, 7):
            self.current_heading_levels[l] = 0
        
        # 构建多级编号 (如 "1.2.3.")
        number_parts = []
        for l in range(1, level + 1):
            if self.current_heading_levels[l] > 0:
                number_parts.append(str(self.current_heading_levels[l]))
        
        return '.'.join(number_parts) + '.'
    
    def _generate_node_id(self) -> str:
        """生成唯一的节点ID"""
        self.node_counter += 1
        return f"node_{self.node_counter}_{uuid.uuid4().hex[:8]}"
    
    def _update_statistics(self, metadata: SIRMetadata, sir_node: SIRNode):
        """更新文档统计信息"""
        def count_nodes(node: SIRNode):
            metadata["stats"]["node_count"] += 1
            
            if node["type"] == NodeType.HEADING:
                metadata["stats"]["heading_count"] += 1
            elif node["type"] == NodeType.PARAGRAPH:
                metadata["stats"]["paragraph_count"] += 1
            elif node["type"] == NodeType.CODE_BLOCK:
                metadata["stats"]["code_block_count"] += 1
            elif node["type"] == NodeType.LIST:
                metadata["stats"]["list_count"] += 1
            elif node["type"] == NodeType.TABLE:
                metadata["stats"]["table_count"] += 1
            
            for child in node.get("children", []):
                count_nodes(child)
        
        count_nodes(sir_node)
    
    def export_to_json(self, sir_document: SIRDocument, indent: int = 2) -> str:
        """将 SIR 文档导出为 JSON"""
        return json.dumps(sir_document, indent=indent, ensure_ascii=False, default=self._json_serializer)
    
    def _json_serializer(self, obj):
        """JSON 序列化辅助函数"""
        if hasattr(obj, 'value'):
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _extract_original_text(self, start_line: int, start_col: int, end_line: int, end_col: int) -> Optional[str]:
        """从原始内容中提取指定位置的文本"""
        if not self.original_content:
            return None
        
        try:
            lines = self.original_content.split('\n')
            
            # 单行情况
            if start_line == end_line:
                line = lines[start_line - 1]
                return line[start_col - 1:end_col - 1]
            
            # 多行情况
            result = []
            
            # 第一行
            first_line = lines[start_line - 1]
            result.append(first_line[start_col - 1:])
            
            # 中间行
            for line_num in range(start_line, end_line - 1):
                result.append(lines[line_num - 1])
            
            # 最后一行
            last_line = lines[end_line - 1]
            result.append(last_line[:end_col - 1])
            
            return '\n'.join(result)
            
        except (IndexError, ValueError):
            return None


def create_sir_converter(config: Optional[SIRConfig] = None) -> SIRConverter:
    """创建 SIR 转换器实例"""
    return SIRConverter(config)


def convert_markdown_to_sir(markdown_content: str, source_file: Optional[str] = None) -> SIRDocument:
    """快速将 Markdown 转换为 SIR"""
    # 解析为 AST
    parser = MarkdownASTParser()
    ast = parser.parse(markdown_content, source_file)
    
    # 转换为 SIR
    converter = SIRConverter()
    return converter.convert(ast, source_file, markdown_content)