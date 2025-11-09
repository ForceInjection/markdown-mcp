"""
SIR (Structured Intermediate Representation) Schema
基于文章《智能体如何高效处理 Markdown：结构化解析与语义编辑方案》的SIR实现

SIR 是一个结构化的中间表示，将Markdown文档转换为语义化的树状结构，
使智能体能够进行语义级别的编辑操作，而不是直接操作文本。
"""

from typing import TypedDict, List, Optional, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum


class NodeType(str, Enum):
    """SIR 节点类型枚举"""
    DOCUMENT = "document"
    SECTION = "section"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    BLOCKQUOTE = "blockquote"
    HR = "hr"
    HTML_BLOCK = "html_block"
    INLINE = "inline"


class HeadingLevel(int, Enum):
    """标题级别枚举"""
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6


class SourcePosition(TypedDict):
    """源代码位置信息"""
    line: int
    column: int
    offset: int


class SourceLocation(TypedDict):
    """源代码位置范围"""
    start: SourcePosition
    end: SourcePosition
    filename: Optional[str]


class SIRMetadata(TypedDict):
    """SIR 元数据"""
    version: str
    generator: str
    created_at: str
    source_file: Optional[str]
    stats: Dict[str, Any]


class SIRNode(TypedDict):
    """SIR 节点基础接口"""
    id: str
    type: NodeType
    content: Optional[str]
    children: List['SIRNode']
    attributes: Dict[str, Any]
    source_location: Optional[SourceLocation]
    parent_id: Optional[str]


class HeadingNode(SIRNode):
    """标题节点"""
    type: Literal[NodeType.HEADING]
    level: HeadingLevel
    title: str
    anchor: Optional[str]
    auto_number: Optional[str]


class ParagraphNode(SIRNode):
    """段落节点"""
    type: Literal[NodeType.PARAGRAPH]


class CodeBlockNode(SIRNode):
    """代码块节点"""
    type: Literal[NodeType.CODE_BLOCK]
    language: Optional[str]
    info: Optional[str]


class ListNode(SIRNode):
    """列表节点"""
    type: Literal[NodeType.LIST]
    ordered: bool
    start: Optional[int]
    tight: bool


class ListItemNode(SIRNode):
    """列表项节点"""
    type: Literal[NodeType.LIST_ITEM]
    checked: Optional[bool]
    spread: bool


class TableNode(SIRNode):
    """表格节点"""
    type: Literal[NodeType.TABLE]
    header: bool
    align: List[Optional[Literal['left', 'right', 'center']]]


class TableRowNode(SIRNode):
    """表格行节点"""
    type: Literal[NodeType.TABLE_ROW]
    is_header: bool


class TableCellNode(SIRNode):
    """表格单元格节点"""
    type: Literal[NodeType.TABLE_CELL]


class BlockquoteNode(SIRNode):
    """引用块节点"""
    type: Literal[NodeType.BLOCKQUOTE]


class SIRDocument(TypedDict):
    """完整的 SIR 文档表示"""
    metadata: SIRMetadata
    ast: SIRNode
    source_map: Dict[str, SourceLocation]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


@dataclass
class SIRConfig:
    """SIR 配置选项"""
    # 是否保留源代码位置信息
    preserve_source_locations: bool = True
    # 是否生成锚点
    generate_anchors: bool = True
    # 是否自动编号标题
    auto_number_headings: bool = False
    # 是否解析内联格式
    parse_inline_formats: bool = True
    # 是否验证文档结构
    validate_structure: bool = True
    # 最大嵌套深度
    max_nesting_depth: int = 20
    # 允许的HTML标签
    allowed_html_tags: List[str] = None

    def __post_init__(self):
        if self.allowed_html_tags is None:
            self.allowed_html_tags = [
                'div', 'span', 'p', 'br', 'hr', 'a', 'img', 'strong', 
                'em', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li'
            ]


# 类型别名，方便使用
SIRNodeType = SIRNode
SIRTree = List[SIRNode]


def create_sir_metadata(source_file: Optional[str] = None) -> SIRMetadata:
    """创建默认的 SIR 元数据"""
    from datetime import datetime
    
    return {
        "version": "1.0.0",
        "generator": "markdown-toc-mcp-sir",
        "created_at": datetime.now().isoformat(),
        "source_file": source_file,
        "stats": {
            "node_count": 0,
            "heading_count": 0,
            "paragraph_count": 0,
            "code_block_count": 0,
            "list_count": 0,
            "table_count": 0
        }
    }