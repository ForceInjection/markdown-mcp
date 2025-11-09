"""
Markdown AST 解析器
基于 markdown-it-py 实现完整的 Markdown 抽象语法树解析

遵循文章《智能体如何高效处理 Markdown：结构化解析与语义编辑方案》的建议，
使用强大的 markdown-it-py 解析器来构建完整的 AST 表示。
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import markdown_it
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from markdown_it.token import Token

from .sir_schema import (
    SIRConfig, SourcePosition, SourceLocation, NodeType, 
    HeadingLevel, SIRNode, SIRMetadata
)


class ASTNodeType(str, Enum):
    """AST 节点类型枚举"""
    ROOT = "root"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    FENCED_CODE = "fenced_code"
    BLOCKQUOTE = "blockquote"
    HR = "hr"
    HTML_BLOCK = "html_block"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    INLINE = "inline"
    TEXT = "text"
    STRONG = "strong"
    EM = "em"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"


@dataclass
class ASTNode:
    """AST 节点表示"""
    type: ASTNodeType
    tag: Optional[str] = None
    content: Optional[str] = None
    children: List['ASTNode'] = None
    attrs: Dict[str, Any] = None
    tokens: List[Token] = None
    source_pos: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.attrs is None:
            self.attrs = {}
        if self.tokens is None:
            self.tokens = []


class MarkdownASTParser:
    """Markdown AST 解析器"""
    
    def __init__(self, config: Optional[SIRConfig] = None):
        self.config = config or SIRConfig()
        self.md = self._create_markdown_it_parser()
    
    def _create_markdown_it_parser(self) -> MarkdownIt:
        """创建配置好的 markdown-it 解析器"""
        return MarkdownIt(
            "commonmark",
            {
                "html": True,
                "linkify": True,
                "typographer": True,
                "breaks": False,
            }
        ).enable('table')
    
    def parse(self, markdown_content: str, source_file: Optional[str] = None) -> ASTNode:
        """解析 Markdown 内容为 AST"""
        try:
            # 解析为 tokens
            tokens = self.md.parse(markdown_content)
            
            # 构建语法树
            syntax_tree = SyntaxTreeNode(tokens)
            
            # 转换为自定义 AST
            ast_root = self._convert_to_ast(syntax_tree, markdown_content)
            
            return ast_root
            
        except Exception as e:
            raise ValueError(f"Failed to parse Markdown: {e}")
    
    def _convert_to_ast(self, syntax_node: SyntaxTreeNode, source: str) -> ASTNode:
        """将 markdown-it 语法树转换为自定义 AST"""
        ast_node = self._create_ast_node_from_syntax_node(syntax_node)
        
        # 递归处理子节点
        for child in syntax_node.children:
            child_ast = self._convert_to_ast(child, source)
            ast_node.children.append(child_ast)
        
        return ast_node
    
    def _create_ast_node_from_syntax_node(self, syntax_node: SyntaxTreeNode) -> ASTNode:
        """根据语法节点创建 AST 节点"""
        node_type = self._map_node_type(syntax_node.type)
        
        # 提取内容
        content = self._extract_content(syntax_node)
        
        # 提取属性
        attrs = self._extract_attributes(syntax_node)
        
        # 提取源代码位置
        source_pos = self._extract_source_position(syntax_node)
        
        # 获取 tokens（如果可用）
        tokens = []
        try:
            # SyntaxTreeNode 没有直接的 tokens 属性，但可以通过 to_tokens() 方法获取
            tokens = syntax_node.to_tokens()
        except (AttributeError, Exception):
            # 如果无法获取 tokens，使用空列表
            pass
        
        return ASTNode(
            type=node_type,
            tag=syntax_node.type,
            content=content,
            attrs=attrs,
            tokens=tokens,
            source_pos=source_pos
        )
    
    def _map_node_type(self, md_type: str) -> ASTNodeType:
        """映射 markdown-it 节点类型到 AST 节点类型"""
        type_mapping = {
            'root': ASTNodeType.ROOT,
            'heading': ASTNodeType.HEADING,
            'paragraph': ASTNodeType.PARAGRAPH,
            'code_block': ASTNodeType.CODE_BLOCK,
            'fenced_code': ASTNodeType.FENCED_CODE,
            'blockquote': ASTNodeType.BLOCKQUOTE,
            'hr': ASTNodeType.HR,
            'html_block': ASTNodeType.HTML_BLOCK,
            'list': ASTNodeType.LIST,
            'list_item': ASTNodeType.LIST_ITEM,
            'table': ASTNodeType.TABLE,
            'table_row': ASTNodeType.TABLE_ROW,
            'table_cell': ASTNodeType.TABLE_CELL,
            'inline': ASTNodeType.INLINE,
            'text': ASTNodeType.TEXT,
            'strong': ASTNodeType.STRONG,
            'em': ASTNodeType.EM,
            'code': ASTNodeType.CODE,
            'link': ASTNodeType.LINK,
            'image': ASTNodeType.IMAGE,
        }
        return type_mapping.get(md_type, ASTNodeType.TEXT)
    
    def _extract_content(self, syntax_node: SyntaxTreeNode) -> Optional[str]:
        """从语法节点提取内容"""
        try:
            tokens = syntax_node.to_tokens()
            if tokens:
                # 对于文本节点，直接返回内容
                if syntax_node.type in ['text', 'inline']:
                    return ' '.join(token.content for token in tokens if token.content)
                
                # 对于代码块，返回代码内容
                if syntax_node.type in ['code_block', 'fenced_code']:
                    for token in tokens:
                        if token.type == 'fence' and token.content:
                            return token.content
                
                # 对于标题节点，从子节点中提取内容
                if syntax_node.type == 'heading':
                    # 标题的内容通常存储在子节点中
                    children = syntax_node.children
                    if children:
                        # 提取所有内联子节点的内容
                        text_contents = []
                        for child in children:
                            if child.type == 'inline':
                                child_tokens = child.to_tokens()
                                if child_tokens:
                                    for token in child_tokens:
                                        # inline token 的 content 字段包含标题文本
                                        if token.content:
                                            text_contents.append(token.content)
                        if text_contents:
                            return ' '.join(text_contents)
        except (AttributeError, Exception):
            pass
        
        return None

    def _extract_attributes(self, syntax_node: SyntaxTreeNode) -> Dict[str, Any]:
        """从语法节点提取属性"""
        attrs = {}
        
        try:
            tokens = syntax_node.to_tokens()
            if tokens:
                for token in tokens:
                    # 提取标题级别
                    if token.type == 'heading_open':
                        match = re.search(r'h([1-6])', token.tag)
                        if match:
                            attrs['level'] = int(match.group(1))
                    
                    # 提取代码语言
                    elif token.type == 'fence' and token.info:
                        attrs['language'] = token.info.strip()
                    
                    # 提取链接信息
                    elif token.type == 'link_open':
                        if token.attrs:
                            for attr_name, attr_value in token.attrs:
                                if attr_name == 'href':
                                    attrs['href'] = attr_value
                                elif attr_name == 'title':
                                    attrs['title'] = attr_value
                    
                    # 提取图片信息
                    elif token.type == 'image':
                        if token.attrs:
                            for attr_name, attr_value in token.attrs:
                                if attr_name == 'src':
                                    attrs['src'] = attr_value
                                elif attr_name == 'alt':
                                    attrs['alt'] = token.content or ""
                                elif attr_name == 'title':
                                    attrs['title'] = attr_value
        except (AttributeError, Exception):
            pass
        
        return attrs
    
    def _extract_source_position(self, syntax_node: SyntaxTreeNode) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """提取源代码位置信息"""
        if not self.config.preserve_source_locations:
            return None
        
        try:
            tokens = syntax_node.to_tokens()
            if tokens:
                first_token = tokens[0]
                last_token = tokens[-1]
                
                if hasattr(first_token, 'map') and first_token.map:
                    start_line = first_token.map[0] + 1  # 转换为1-based
                    end_line = last_token.map[1] if hasattr(last_token, 'map') and last_token.map else start_line
                    
                    return ((start_line, 1), (end_line, 1))
        except (AttributeError, Exception):
            pass
        
        return None
    
    def analyze_ast_structure(self, ast_node: ASTNode) -> Dict[str, Any]:
        """分析 AST 结构统计信息"""
        stats = {
            'total_nodes': 0,
            'by_type': {},
            'max_depth': 0,
            'headings_by_level': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
            'code_blocks': 0,
            'lists': 0,
            'tables': 0,
            'links': 0,
            'images': 0
        }
        
        self._traverse_ast_for_stats(ast_node, stats, 0)
        return stats
    
    def _traverse_ast_for_stats(self, node: ASTNode, stats: Dict[str, Any], depth: int):
        """遍历 AST 收集统计信息"""
        stats['total_nodes'] += 1
        stats['max_depth'] = max(stats['max_depth'], depth)
        
        # 按类型统计
        node_type = node.type.value
        stats['by_type'][node_type] = stats['by_type'].get(node_type, 0) + 1
        
        # 特定类型统计
        if node.type == ASTNodeType.HEADING:
            level = node.attrs.get('level', 1)
            if 1 <= level <= 6:
                stats['headings_by_level'][level] += 1
        elif node.type in [ASTNodeType.CODE_BLOCK, ASTNodeType.FENCED_CODE]:
            stats['code_blocks'] += 1
        elif node.type == ASTNodeType.LIST:
            stats['lists'] += 1
        elif node.type == ASTNodeType.TABLE:
            stats['tables'] += 1
        elif node.type == ASTNodeType.LINK:
            stats['links'] += 1
        elif node.type == ASTNodeType.IMAGE:
            stats['images'] += 1
        
        # 递归处理子节点
        for child in node.children:
            self._traverse_ast_for_stats(child, stats, depth + 1)
    
    def find_nodes_by_type(self, ast_node: ASTNode, target_type: ASTNodeType) -> List[ASTNode]:
        """查找特定类型的节点"""
        results = []
        self._find_nodes_recursive(ast_node, target_type, results)
        return results
    
    def _find_nodes_recursive(self, node: ASTNode, target_type: ASTNodeType, results: List[ASTNode]):
        """递归查找节点"""
        if node.type == target_type:
            results.append(node)
        
        for child in node.children:
            self._find_nodes_recursive(child, target_type, results)
    
    def get_heading_structure(self, ast_node: ASTNode) -> List[Dict[str, Any]]:
        """获取标题结构信息"""
        headings = self.find_nodes_by_type(ast_node, ASTNodeType.HEADING)
        
        result = []
        for heading in headings:
            result.append({
                'level': heading.attrs.get('level', 1),
                'title': heading.content or '',
                'source_position': heading.source_pos,
                'attributes': heading.attrs
            })
        
        return result


def create_ast_parser(config: Optional[SIRConfig] = None) -> MarkdownASTParser:
    """创建 AST 解析器实例"""
    return MarkdownASTParser(config)


def parse_markdown_to_ast(markdown_content: str, source_file: Optional[str] = None) -> ASTNode:
    """快速解析 Markdown 到 AST"""
    parser = MarkdownASTParser()
    return parser.parse(markdown_content, source_file)