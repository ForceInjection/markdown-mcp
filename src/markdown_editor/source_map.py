"""
Source Map 机制

记录原始 Markdown 文档与 SIR 节点之间的位置映射关系，
支持双向位置转换和编辑操作的源位置追踪。

遵循文章《智能体如何高效处理 Markdown：结构化解析与语义编辑方案》的设计理念。
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import re
from enum import Enum

from .sir_schema import SIRNode, SourceLocation, SourcePosition


class MappingType(str, Enum):
    """映射类型枚举"""
    EXACT = "exact"          # 精确匹配
    APPROXIMATE = "approximate"  # 近似匹配
    GENERATED = "generated"   # 生成的内容
    DELETED = "deleted"       # 已删除的内容


@dataclass
class SourceMapping:
    """源映射条目"""
    sir_node_id: str
    original_text: str
    original_location: SourceLocation
    mapping_type: MappingType
    confidence: float  # 映射置信度 (0.0 - 1.0)
    metadata: Dict[str, Any]


@dataclass
class EditOperationMapping:
    """编辑操作映射"""
    operation_id: str
    operation_type: str
    sir_node_ids: List[str]
    original_locations: List[SourceLocation]
    new_content: str
    timestamp: float
    user: Optional[str] = None


class SourceMap:
    """Source Map 管理器"""
    
    def __init__(self, original_content: str, source_file: Optional[str] = None):
        self.original_content = original_content
        self.source_file = source_file
        self.mappings: Dict[str, SourceMapping] = {}  # sir_node_id -> mapping
        self.edit_history: List[EditOperationMapping] = []
        self.line_offsets: List[int] = self._calculate_line_offsets(original_content)
    
    def add_mapping(self, sir_node: SIRNode, original_text: str, 
                   start_line: int, start_col: int, end_line: int, end_col: int,
                   mapping_type: MappingType = MappingType.EXACT,
                   confidence: float = 1.0,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """添加源映射"""
        try:
            node_id = sir_node.get("id")
            if not node_id:
                return False
            
            location = SourceLocation(
                file=self.source_file,
                start=SourcePosition(line=start_line, column=start_col, offset=0),
                end=SourcePosition(line=end_line, column=end_col, offset=0)
            )
            
            mapping = SourceMapping(
                sir_node_id=node_id,
                original_text=original_text,
                original_location=location,
                mapping_type=mapping_type,
                confidence=confidence,
                metadata=metadata or {}
            )
            
            self.mappings[node_id] = mapping
            
            # 更新节点的源位置信息
            sir_node["source_location"] = location
            
            return True
            
        except Exception:
            return False
    
    def get_mapping(self, sir_node_id: str) -> Optional[SourceMapping]:
        """获取节点的源映射"""
        return self.mappings.get(sir_node_id)
    
    def find_mapping_by_position(self, line: int, col: int) -> Optional[SourceMapping]:
        """根据源文件位置查找映射"""
        for mapping in self.mappings.values():
            loc = mapping.original_location
            if (loc.start.line <= line <= loc.end.line and
                (loc.start.line != line or loc.start.column <= col) and
                (loc.end.line != line or loc.end.column >= col)):
                return mapping
        return None
    
    def find_mapping_by_text(self, text: str, exact_match: bool = True) -> List[SourceMapping]:
        """根据文本内容查找映射"""
        results = []
        for mapping in self.mappings.values():
            if exact_match:
                if mapping.original_text == text:
                    results.append(mapping)
            else:
                if text in mapping.original_text:
                    results.append(mapping)
        return results
    
    def record_edit_operation(self, operation_type: str, sir_node_ids: List[str],
                             new_content: str, user: Optional[str] = None) -> str:
        """记录编辑操作"""
        import time
        import uuid
        
        # 收集原始位置信息
        original_locations = []
        for node_id in sir_node_ids:
            mapping = self.get_mapping(node_id)
            if mapping:
                original_locations.append(mapping.original_location)
        
        operation_id = f"edit_{uuid.uuid4().hex[:8]}"
        
        edit_op = EditOperationMapping(
            operation_id=operation_id,
            operation_type=operation_type,
            sir_node_ids=sir_node_ids,
            original_locations=original_locations,
            new_content=new_content,
            timestamp=time.time(),
            user=user
        )
        
        self.edit_history.append(edit_op)
        return operation_id
    
    def get_edit_history(self) -> List[EditOperationMapping]:
        """获取编辑历史"""
        return self.edit_history
    
    def get_original_text(self, sir_node_id: str) -> Optional[str]:
        """获取节点的原始文本"""
        mapping = self.get_mapping(sir_node_id)
        return mapping.original_text if mapping else None
    
    def get_original_location(self, sir_node_id: str) -> Optional[SourceLocation]:
        """获取节点的原始位置"""
        mapping = self.get_mapping(sir_node_id)
        return mapping.original_location if mapping else None
    
    def update_mapping_after_edit(self, sir_node_id: str, new_text: str,
                                 new_start_line: int, new_start_col: int,
                                 new_end_line: int, new_end_col: int) -> bool:
        """编辑后更新映射"""
        mapping = self.get_mapping(sir_node_id)
        if not mapping:
            return False
        
        # 创建新的位置信息
        new_location = SourceLocation(
            file=self.source_file,
            start=SourcePosition(line=new_start_line, column=new_start_col, offset=0),
            end=SourcePosition(line=new_end_line, column=new_end_col, offset=0)
        )
        
        # 更新映射
        mapping.original_text = new_text
        mapping.original_location = new_location
        mapping.mapping_type = MappingType.GENERATED
        mapping.confidence = 0.8  # 降低置信度
        
        return True
    
    def calculate_position_offset(self, line: int, col: int, 
                                content_delta: int) -> Tuple[int, int]:
        """计算内容变化后的位置偏移"""
        # 简单的实现：假设编辑发生在特定位置
        # 在实际应用中应该更复杂
        return line, col
    
    def get_text_at_location(self, location: SourceLocation) -> str:
        """获取指定位置的原始文本"""
        try:
            lines = self.original_content.split('\n')
            
            if location.start.line == location.end.line:
                # 单行范围
                line = lines[location.start.line - 1]
                return line[location.start.column - 1:location.end.column]
            else:
                # 多行范围
                result = []
                
                # 第一行
                first_line = lines[location.start.line - 1]
                result.append(first_line[location.start.column - 1:])
                
                # 中间行
                for line_num in range(location.start.line, location.end.line - 1):
                    result.append(lines[line_num])
                
                # 最后一行
                last_line = lines[location.end.line - 1]
                result.append(last_line[:location.end.column])
                
                return '\n'.join(result)
                
        except IndexError:
            return ""
    
    def _calculate_line_offsets(self, content: str) -> List[int]:
        """计算每行的偏移量"""
        offsets = [0]
        offset = 0
        
        for char in content:
            offset += 1
            if char == '\n':
                offsets.append(offset)
        
        return offsets
    
    def get_line_offset(self, line_number: int) -> int:
        """获取指定行的偏移量"""
        if 1 <= line_number <= len(self.line_offsets):
            return self.line_offsets[line_number - 1]
        return 0
    
    def find_node_by_original_text(self, text: str) -> List[str]:
        """根据原始文本查找节点ID"""
        results = []
        for node_id, mapping in self.mappings.items():
            if mapping.original_text == text:
                results.append(node_id)
        return results
    
    def get_coverage_statistics(self) -> Dict[str, Any]:
        """获取映射覆盖统计信息"""
        total_chars = len(self.original_content)
        mapped_chars = 0
        
        for mapping in self.mappings.values():
            loc = mapping.original_location
            # 计算映射的字符数（简化计算）
            if loc.start.line == loc.end.line:
                mapped_chars += (loc.end.column - loc.start.column + 1)
            else:
                # 多行映射，近似计算
                mapped_chars += 100  # 近似值
        
        coverage = (mapped_chars / total_chars) * 100 if total_chars > 0 else 0
        
        return {
            "total_characters": total_chars,
            "mapped_characters": mapped_chars,
            "coverage_percentage": round(coverage, 2),
            "total_mappings": len(self.mappings),
            "exact_mappings": sum(1 for m in self.mappings.values() 
                                 if m.mapping_type == MappingType.EXACT),
            "approximate_mappings": sum(1 for m in self.mappings.values() 
                                       if m.mapping_type == MappingType.APPROXIMATE),
            "generated_mappings": sum(1 for m in self.mappings.values() 
                                     if m.mapping_type == MappingType.GENERATED)
        }

    def to_dict(self) -> Dict[str, Any]:
        """将 SourceMap 转换为字典格式"""
        return {
            "original_content": self.original_content,
            "source_file": self.source_file,
            "mappings": {
                node_id: {
                    "original_text": mapping.original_text,
                    "original_location": {
                        "file": mapping.original_location["file"],
                        "start": {
                            "line": mapping.original_location["start"]["line"],
                            "column": mapping.original_location["start"]["column"],
                            "offset": mapping.original_location["start"]["offset"]
                        },
                        "end": {
                            "line": mapping.original_location["end"]["line"],
                            "column": mapping.original_location["end"]["column"],
                            "offset": mapping.original_location["end"]["offset"]
                        }
                    },
                    "mapping_type": mapping.mapping_type.value,
                    "confidence": mapping.confidence,
                    "metadata": mapping.metadata
                }
                for node_id, mapping in self.mappings.items()
            },
            "edit_history": [
                {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type,
                    "sir_node_ids": op.sir_node_ids,
                    "original_locations": [
                        {
                            "file": loc["file"],
                            "start": {
                                "line": loc["start"]["line"],
                                "column": loc["start"]["column"],
                                "offset": loc["start"]["offset"]
                            },
                            "end": {
                                "line": loc["end"]["line"],
                                "column": loc["end"]["column"],
                                "offset": loc["end"]["offset"]
                            }
                        }
                        for loc in op.original_locations
                    ],
                    "new_content": op.new_content,
                    "timestamp": op.timestamp,
                    "user": op.user
                }
                for op in self.edit_history
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceMap':
        """从字典格式创建 SourceMap 实例"""
        source_map = cls(data["original_content"], data.get("source_file"))
        
        # 恢复映射
        for node_id, mapping_data in data.get("mappings", {}).items():
            loc_data = mapping_data["original_location"]
            start_data = loc_data["start"]
            end_data = loc_data["end"]
            
            mapping = SourceMapping(
                sir_node_id=node_id,
                original_text=mapping_data["original_text"],
                original_location=SourceLocation(
                    file=loc_data["file"],
                    start=SourcePosition(
                        line=start_data["line"],
                        column=start_data["column"],
                        offset=start_data.get("offset", 0)
                    ),
                    end=SourcePosition(
                        line=end_data["line"],
                        column=end_data["column"],
                        offset=end_data.get("offset", 0)
                    )
                ),
                mapping_type=MappingType(mapping_data["mapping_type"]),
                confidence=mapping_data["confidence"],
                metadata=mapping_data.get("metadata", {})
            )
            source_map.mappings[node_id] = mapping
        
        # 恢复编辑历史
        for op_data in data.get("edit_history", []):
            op = EditOperationMapping(
                operation_id=op_data["operation_id"],
                operation_type=op_data["operation_type"],
                sir_node_ids=op_data["sir_node_ids"],
                original_locations=[
                    SourceLocation(
                        file=loc_data["file"],
                        start=SourcePosition(
                            line=loc_data["start"]["line"],
                            column=loc_data["start"]["column"],
                            offset=loc_data["start"].get("offset", 0)
                        ),
                        end=SourcePosition(
                            line=loc_data["end"]["line"],
                            column=loc_data["end"]["column"],
                            offset=loc_data["end"].get("offset", 0)
                        )
                    )
                    for loc_data in op_data["original_locations"]
                ],
                new_content=op_data["new_content"],
                timestamp=op_data["timestamp"],
                user=op_data.get("user")
            )
            source_map.edit_history.append(op)
        
        return source_map


def create_source_map(original_content: str, source_file: Optional[str] = None) -> SourceMap:
    """创建 Source Map 实例"""
    return SourceMap(original_content, source_file)


def calculate_source_position(content: str, char_offset: int) -> SourcePosition:
    """计算字符偏移量对应的源位置"""
    line = 1
    col = 1
    current_offset = 0
    
    for char in content:
        if current_offset >= char_offset:
            break
        
        if char == '\n':
            line += 1
            col = 1
        else:
            col += 1
        
        current_offset += 1
    
    return SourcePosition(line=line, column=col)


def find_text_in_content(content: str, search_text: str, 
                        start_line: int = 1, start_col: int = 1) -> Optional[SourceLocation]:
    """在内容中查找文本并返回位置"""
    lines = content.split('\n')
    
    # 从指定位置开始搜索
    for line_idx in range(start_line - 1, len(lines)):
        line = lines[line_idx]
        
        # 确定起始列
        start_search_col = start_col if line_idx == start_line - 1 else 1
        
        pos = line.find(search_text, start_search_col - 1)
        if pos != -1:
            return SourceLocation(
                file=None,
                start=SourcePosition(line=line_idx + 1, column=pos + 1),
                end=SourcePosition(line=line_idx + 1, column=pos + len(search_text) + 1)
            )
    
    return None