"""
语义化编辑接口

基于 SIR (Structured Intermediate Representation) 提供语义级别的 Markdown 编辑操作，
使智能体能够直接操作文档结构而不是原始文本。

遵循文章《智能体如何高效处理 Markdown：结构化解析与语义编辑方案》的设计理念。
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import re
import uuid
from enum import Enum

from .sir_schema import (
    SIRDocument, SIRNode, NodeType, HeadingLevel, HeadingNode, ParagraphNode,
    CodeBlockNode, ListNode, ListItemNode, TableNode, SourceLocation, SIRConfig
)
from .sir_converter import SIRConverter
from .source_map import SourceMap, MappingType, EditOperationMapping


class EditOperation(str, Enum):
    """编辑操作类型枚举"""
    UPDATE_HEADING = "update_heading"
    INSERT_SECTION = "insert_section"
    DELETE_SECTION = "delete_section"
    MOVE_SECTION = "move_section"
    UPDATE_CONTENT = "update_content"
    ADD_PARAGRAPH = "add_paragraph"
    ADD_CODE_BLOCK = "add_code_block"
    ADD_LIST = "add_list"
    ADD_TABLE = "add_table"
    RENUMBER_HEADINGS = "renumber_headings"
    FIX_NUMBERING = "fix_numbering"
    CHECK_CONSISTENCY = "check_consistency"
    AUTO_REPAIR = "auto_repair"


class EditPosition(str, Enum):
    """编辑位置枚举"""
    BEFORE = "before"
    AFTER = "after"
    CHILD = "child"
    REPLACE = "replace"


@dataclass
class EditResult:
    """编辑操作结果"""
    success: bool
    message: str
    changes: List[Dict[str, Any]]
    warnings: List[str]
    errors: List[str]


class SemanticEditor:
    """语义化编辑器"""
    
    def __init__(self, sir_document: SIRDocument, config: Optional[SIRConfig] = None):
        self.document = sir_document
        self.config = config or SIRConfig()
        self.edit_history: List[Dict[str, Any]] = []
        self.source_map: Optional[SourceMap] = None
        
        # 从文档中提取Source Map
        if "source_map" in sir_document and sir_document["source_map"]:
            self.source_map = SourceMap.from_dict(sir_document["source_map"])
    
    def update_heading(self, node_id: str, new_title: str, 
                      new_level: Optional[int] = None) -> EditResult:
        """更新标题内容和/或级别"""
        try:
            # 查找节点
            node = self._find_node_by_id(node_id)
            if not node or node["type"] != NodeType.HEADING:
                return EditResult(
                    success=False,
                    message=f"Node {node_id} is not a heading or not found",
                    changes=[],
                    warnings=[],
                    errors=[f"Heading node {node_id} not found"]
                )
            
            # 记录原始值
            old_title = node.get("title", "")
            old_level = node.get("level", 1)
            
            # 更新标题
            node["title"] = new_title
            node["content"] = new_title
            
            # 更新级别（如果提供）
            if new_level is not None and 1 <= new_level <= 6:
                node["level"] = HeadingLevel(new_level)
            
            # 重新生成锚点
            if self.config.generate_anchors:
                clean_title = self._clean_title_text(new_title)
                node["anchor"] = self._generate_anchor(clean_title)
            
            # 记录编辑历史
            change = {
                "operation": EditOperation.UPDATE_HEADING,
                "node_id": node_id,
                "changes": {
                    "title": {"old": old_title, "new": new_title},
                    "level": {"old": old_level, "new": new_level or old_level}
                }
            }
            self.edit_history.append(change)
            
            return EditResult(
                success=True,
                message=f"Heading updated successfully",
                changes=[change],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return EditResult(
                success=False,
                message=f"Failed to update heading: {e}",
                changes=[],
                warnings=[],
                errors=[str(e)]
            )
    
    def insert_section(self, parent_id: str, position: EditPosition, 
                      title: str, level: int = 2, content: Optional[str] = None) -> EditResult:
        """插入新的章节"""
        try:
            # 查找父节点
            parent_node = self._find_node_by_id(parent_id)
            if not parent_node:
                return EditResult(
                    success=False,
                    message=f"Parent node {parent_id} not found",
                    changes=[],
                    warnings=[],
                    errors=[f"Parent node {parent_id} not found"]
                )
            
            # 创建新的标题节点
            new_heading = self._create_heading_node(title, level)
            
            # 创建内容节点（如果有内容）并添加到标题节点的子节点
            if content:
                paragraph_node = self._create_paragraph_node(content)
                new_heading["children"].append(paragraph_node)
            
            # 根据位置插入
            if position == EditPosition.CHILD:
                # 作为子节点插入
                if "children" not in parent_node:
                    parent_node["children"] = []
                parent_node["children"].insert(0, new_heading)
                # 设置父节点ID
                new_heading["parent_id"] = parent_id
            else:
                # 查找父节点的父节点（祖父节点）
                grandparent = self._find_parent_node(parent_node["id"])
                
                if not grandparent:
                    # 如果父节点是文档节点（没有祖父节点），则在文档节点的子节点列表中插入
                    if parent_node.get("type") == NodeType.DOCUMENT:
                        # 在文档节点的子节点列表中插入
                        sibling_index = self._find_node_index_in_parent(parent_id)
                        if sibling_index == -1:
                            return EditResult(
                                success=False,
                                message="Cannot determine sibling position",
                                changes=[],
                                warnings=[],
                                errors=["Sibling position not found"]
                            )
                        
                        # 确保文档节点有 children 列表
                        if "children" not in parent_node:
                            parent_node["children"] = []
                        
                        if position == EditPosition.BEFORE:
                            parent_node["children"].insert(sibling_index, new_heading)
                        elif position == EditPosition.AFTER:
                            parent_node["children"].insert(sibling_index + 1, new_heading)
                        # 设置父节点ID
                        new_heading["parent_id"] = parent_node["id"]
                    else:
                        return EditResult(
                            success=False,
                            message="Cannot find parent's parent for insertion",
                            changes=[],
                            warnings=[],
                            errors=["Parent's parent not found"]
                        )
                else:
                    # 在父节点的兄弟位置插入
                    sibling_index = self._find_node_index_in_parent(parent_id)
                    if sibling_index == -1:
                        return EditResult(
                            success=False,
                            message="Cannot determine sibling position",
                            changes=[],
                            warnings=[],
                            errors=["Sibling position not found"]
                        )
                    
                    if position == EditPosition.BEFORE:
                        grandparent["children"].insert(sibling_index, new_heading)
                    elif position == EditPosition.AFTER:
                        grandparent["children"].insert(sibling_index + 1, new_heading)
                    # 设置父节点ID
                    new_heading["parent_id"] = grandparent["id"]
            
            # 记录编辑历史
            change = {
                "operation": EditOperation.INSERT_SECTION,
                "new_node_id": new_heading["id"],
                "parent_id": parent_id,
                "position": position,
                "title": title,
                "level": level
            }
            self.edit_history.append(change)
            
            return EditResult(
                success=True,
                message=f"Section inserted successfully",
                changes=[change],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return EditResult(
                success=False,
                message=f"Failed to insert section: {e}",
                changes=[],
                warnings=[],
                errors=[str(e)]
            )
    
    def delete_section(self, node_id: str) -> EditResult:
        """删除章节"""
        try:
            # 查找节点
            node = self._find_node_by_id(node_id)
            if not node:
                return EditResult(
                    success=False,
                    message=f"Node {node_id} not found",
                    changes=[],
                    warnings=[],
                    errors=[f"Node {node_id} not found"]
                )
            
            # 查找父节点
            parent = self._find_parent_node(node_id)
            if not parent:
                return EditResult(
                    success=False,
                    message="Cannot find parent node",
                    changes=[],
                    warnings=[],
                    errors=["Parent node not found"]
                )
            
            # 记录被删除的节点信息
            deleted_info = {
                "id": node["id"],
                "type": node["type"],
                "title": node.get("title", ""),
                "content": node.get("content", "")[:100]  # 只记录前100个字符
            }
            
            # 从父节点中移除
            parent["children"] = [child for child in parent.get("children", []) 
                                 if child["id"] != node_id]
            
            # 记录编辑历史
            change = {
                "operation": EditOperation.DELETE_SECTION,
                "deleted_node": deleted_info,
                "parent_id": parent["id"]
            }
            self.edit_history.append(change)
            
            return EditResult(
                success=True,
                message=f"Section deleted successfully",
                changes=[change],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return EditResult(
                success=False,
                message=f"Failed to delete section: {e}",
                changes=[],
                warnings=[],
                errors=[str(e)]
            )
    
    def move_section(self, node_id: str, new_parent_id: str, 
                    position: EditPosition = EditPosition.CHILD) -> EditResult:
        """移动章节到新位置"""
        try:
            # 查找节点和新父节点
            node = self._find_node_by_id(node_id)
            new_parent = self._find_node_by_id(new_parent_id)
            
            if not node or not new_parent:
                return EditResult(
                    success=False,
                    message="Node or new parent not found",
                    changes=[],
                    warnings=[],
                    errors=["Node or new parent not found"]
                )
            
            # 从原父节点中移除
            old_parent = self._find_parent_node(node_id)
            if old_parent:
                old_parent["children"] = [child for child in old_parent.get("children", []) 
                                       if child["id"] != node_id]
            
            # 添加到新父节点
            if "children" not in new_parent:
                new_parent["children"] = []
            
            if position == EditPosition.CHILD:
                new_parent["children"].append(node)
            else:
                # 处理兄弟位置
                if position == EditPosition.BEFORE:
                    new_parent["children"].insert(0, node)
                elif position == EditPosition.AFTER:
                    if new_parent["children"]:
                        new_parent["children"].append(node)
                    else:
                        new_parent["children"].insert(0, node)
            
            # 更新父节点引用
            node["parent_id"] = new_parent_id
            
            # 记录编辑历史
            change = {
                "operation": EditOperation.MOVE_SECTION,
                "node_id": node_id,
                "old_parent_id": old_parent["id"] if old_parent else None,
                "new_parent_id": new_parent_id,
                "position": position
            }
            self.edit_history.append(change)
            
            return EditResult(
                success=True,
                message=f"Section moved successfully",
                changes=[change],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return EditResult(
                success=False,
                message=f"Failed to move section: {e}",
                changes=[],
                warnings=[],
                errors=[str(e)]
            )
    
    def update_content(self, node_id: str, new_content: str) -> EditResult:
        """更新节点内容"""
        try:
            node = self._find_node_by_id(node_id)
            if not node:
                return EditResult(
                    success=False,
                    message=f"Node {node_id} not found",
                    changes=[],
                    warnings=[],
                    errors=[f"Node {node_id} not found"]
                )
            
            # 记录原始内容
            old_content = node.get("content", "")
            
            # 更新内容
            node["content"] = new_content
            
            # 对于标题节点，同时更新title
            if node["type"] == NodeType.HEADING:
                node["title"] = new_content
                # 重新生成锚点
                if self.config.generate_anchors:
                    clean_title = self._clean_title_text(new_content)
                    node["anchor"] = self._generate_anchor(clean_title)
            
            # 记录编辑历史
            change = {
                "operation": EditOperation.UPDATE_CONTENT,
                "node_id": node_id,
                "content_type": node["type"],
                "changes": {
                    "content": {"old": old_content, "new": new_content}
                }
            }
            self.edit_history.append(change)
            
            return EditResult(
                success=True,
                message=f"Content updated successfully",
                changes=[change],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return EditResult(
                success=False,
                message=f"Failed to update content: {e}",
                changes=[],
                warnings=[],
                errors=[str(e)]
            )
    
    def add_paragraph(self, parent_id: str, content: str, 
                     position: EditPosition = EditPosition.CHILD) -> EditResult:
        """添加段落"""
        try:
            parent_node = self._find_node_by_id(parent_id)
            if not parent_node:
                return EditResult(
                    success=False,
                    message=f"Parent node {parent_id} not found",
                    changes=[],
                    warnings=[],
                    errors=[f"Parent node {parent_id} not found"]
                )
            
            # 创建段落节点
            paragraph_node = self._create_paragraph_node(content)
            
            # 添加到父节点
            if "children" not in parent_node:
                parent_node["children"] = []
            
            parent_node["children"].append(paragraph_node)
            
            # 记录编辑历史
            change = {
                "operation": EditOperation.ADD_PARAGRAPH,
                "new_node_id": paragraph_node["id"],
                "parent_id": parent_id,
                "content": content
            }
            self.edit_history.append(change)
            
            return EditResult(
                success=True,
                message=f"Paragraph added successfully",
                changes=[change],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return EditResult(
                success=False,
                message=f"Failed to add paragraph: {e}",
                changes=[],
                warnings=[],
                errors=[str(e)]
            )
    
    def renumber_headings(self) -> EditResult:
        """重新编号所有标题"""
        try:
            # 获取所有标题
            headings = self._find_nodes_by_type(NodeType.HEADING)
            
            # 按级别分组并排序
            headings_by_level = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
            for heading in headings:
                level = heading.get("level", 1)
                if 1 <= level <= 6:
                    headings_by_level[level].append(heading)
            
            changes = []
            
            # 重新编号各级标题
            for level in range(1, 7):
                level_headings = headings_by_level[level]
                for i, heading in enumerate(level_headings, 1):
                    old_number = heading.get("auto_number", "")
                    new_number = self._generate_hierarchical_number(heading, i)
                    
                    if old_number != new_number:
                        heading["auto_number"] = new_number
                        changes.append({
                            "node_id": heading["id"],
                            "level": level,
                            "old_number": old_number,
                            "new_number": new_number
                        })
            
            # 记录编辑历史
            if changes:
                change_record = {
                    "operation": EditOperation.RENUMBER_HEADINGS,
                    "changes": changes
                }
                self.edit_history.append(change_record)
            
            return EditResult(
                success=True,
                message=f"Headings renumbered: {len(changes)} changes made",
                changes=[{"operation": EditOperation.RENUMBER_HEADINGS, "changes": changes}] if changes else [],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            return EditResult(
                success=False,
                message=f"Failed to renumber headings: {e}",
                changes=[],
                warnings=[],
                errors=[str(e)]
            )
    
    def _generate_hierarchical_number(self, heading: HeadingNode, index: int) -> str:
        """生成层次化编号"""
        # 简单的层次化编号实现
        # 在实际应用中应该基于父级标题的编号
        level = heading.get("level", 1)
        return ".".join(str(index) for _ in range(level))
    
    def _create_heading_node(self, title: str, level: int = 2) -> HeadingNode:
        """创建标题节点"""
        clean_title = self._clean_title_text(title)
        anchor = self._generate_anchor(clean_title) if self.config.generate_anchors else None
        
        return {
            "id": self._generate_node_id(),
            "type": NodeType.HEADING,
            "content": clean_title,
            "children": [],
            "attributes": {},
            "source_location": None,
            "parent_id": None,
            "level": HeadingLevel(level),
            "title": clean_title,
            "anchor": anchor,
            "auto_number": None
        }
    
    def _create_paragraph_node(self, content: str) -> ParagraphNode:
        """创建段落节点"""
        return {
            "id": self._generate_node_id(),
            "type": NodeType.PARAGRAPH,
            "content": content,
            "children": [],
            "attributes": {},
            "source_location": None,
            "parent_id": None
        }
    
    def _find_node_by_id(self, node_id: str) -> Optional[SIRNode]:
        """根据ID查找节点"""
        def search_node(node: SIRNode) -> Optional[SIRNode]:
            if node["id"] == node_id:
                return node
            for child in node.get("children", []):
                found = search_node(child)
                if found:
                    return found
            return None
        
        return search_node(self.document["ast"])
    
    def _find_parent_node(self, node_id: str) -> Optional[SIRNode]:
        """查找父节点"""
        target_node = self._find_node_by_id(node_id)
        if not target_node or "parent_id" not in target_node:
            return None
        
        parent_id = target_node["parent_id"]
        if not parent_id:
            return None
        
        return self._find_node_by_id(parent_id)
    
    def _find_node_index_in_parent(self, node_id: str) -> int:
        """查找节点在父节点中的索引"""
        parent = self._find_parent_node(node_id)
        if not parent or "children" not in parent:
            return -1
        
        for i, child in enumerate(parent["children"]):
            if child["id"] == node_id:
                return i
        
        return -1
    
    def _find_nodes_by_type(self, node_type: NodeType) -> List[SIRNode]:
        """查找特定类型的所有节点"""
        results = []
        
        def search_nodes(node: SIRNode):
            if node["type"] == node_type:
                results.append(node)
            for child in node.get("children", []):
                search_nodes(child)
        
        search_nodes(self.document["ast"])
        return results
    
    def _clean_title_text(self, title: str) -> str:
        """清理标题文本"""
        clean_title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)  # 粗体
        clean_title = re.sub(r'\*(.*?)\*', r'\1', clean_title)    # 斜体
        clean_title = re.sub(r'`(.*?)`', r'\1', clean_title)      # 代码
        clean_title = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', clean_title)  # 链接
        return clean_title.strip()
    
    def _generate_anchor(self, title: str) -> str:
        """生成URL友好的锚点"""
        anchor = title.lower()
        anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
        anchor = re.sub(r'[\s-]+', '-', anchor)
        return anchor.strip('-')
    
    def _generate_node_id(self) -> str:
        """生成唯一的节点ID"""
        return f"node_{uuid.uuid4().hex[:12]}"
    
    def get_edit_history(self) -> List[Dict[str, Any]]:
        """获取编辑历史"""
        return self.edit_history
    
    def clear_history(self):
        """清空编辑历史"""
        self.edit_history.clear()
    
    def get_document(self) -> SIRDocument:
        """获取当前文档"""
        return self.document
    
    def check_consistency(self) -> Dict[str, Any]:
        """
        执行文档一致性检查
        
        Returns:
            Dict[str, Any]: 包含所有检查结果的字典
        """
        checker = ConsistencyChecker(self)
        return checker.check_all()
    
    def auto_repair(self) -> Dict[str, Any]:
        """
        执行自动修复
        
        Returns:
            Dict[str, Any]: 包含修复结果的字典
        """
        repairer = AutoRepair(self)
        return repairer.repair_all()


def create_semantic_editor(sir_document: SIRDocument, 
                          config: Optional[SIRConfig] = None) -> SemanticEditor:
    """创建语义化编辑器实例"""
    return SemanticEditor(sir_document, config)


def create_editor_from_markdown(markdown_content: str, 
                               source_file: Optional[str] = None) -> SemanticEditor:
    """从 Markdown 内容创建编辑器"""
    from .sir_converter import convert_markdown_to_sir
    sir_doc = convert_markdown_to_sir(markdown_content, source_file)
    return SemanticEditor(sir_doc)


# 一致性检查和自动修复功能实现
class ConsistencyChecker:
    """一致性检查器 - 提供文档结构和内容的完整性检查"""
    
    def __init__(self, editor: SemanticEditor):
        self.editor = editor
    
    def check_all(self) -> Dict[str, Any]:
        """执行所有一致性检查"""
        results = {
            "heading_numbering": self.check_heading_numbering(),
            "structure_integrity": self.check_structure_integrity(),
            "content_format": self.check_content_format(),
            "link_integrity": self.check_link_integrity(),
            "metadata_completeness": self.check_metadata_completeness()
        }
        
        # 计算总体状态
        all_issues = []
        for check_name, result in results.items():
            if result["has_issues"]:
                all_issues.extend(result["issues"])
        
        results["overall"] = {
            "has_issues": len(all_issues) > 0,
            "total_issues": len(all_issues),
            "issue_categories": [name for name, result in results.items() if result["has_issues"]]
        }
        
        return results
    
    def check_heading_numbering(self) -> Dict[str, Any]:
        """检查标题编号一致性"""
        issues = []
        headings = self.editor._find_nodes_by_type(NodeType.HEADING)
        
        # 按级别分组
        level_groups = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        for heading in headings:
            level = heading.get("level", 1)
            if 1 <= level <= 6:
                level_groups[level].append(heading)
        
        # 检查重复编号
        for level, level_headings in level_groups.items():
            seen_numbers = {}
            for heading in level_headings:
                number = heading.get("auto_number", "")
                if number and number in seen_numbers:
                    issues.append({
                        "type": "duplicate_number",
                        "level": level,
                        "number": number,
                        "node_id": heading["id"],
                        "title": heading.get("title", ""),
                        "message": f"级别 {level} 的编号 {number} 重复出现"
                    })
                seen_numbers[number] = heading
        
        # 检查编号连续性
        for level, level_headings in level_groups.items():
            numbered_headings = [h for h in level_headings if h.get("auto_number")]
            if numbered_headings:
                numbers = []
                for heading in numbered_headings:
                    try:
                        # 尝试解析编号（支持 1, 1.1, 1.2.3 等格式）
                        number_parts = heading["auto_number"].split('.')
                        if all(part.isdigit() for part in number_parts):
                            numbers.append((heading, [int(part) for part in number_parts]))
                    except (ValueError, AttributeError):
                        continue
                
                # 检查连续性
                if numbers:
                    # 按编号排序
                    numbers.sort(key=lambda x: x[1])
                    
                    # 检查简单编号连续性
                    if len(numbers[0][1]) == 1:  # 单级编号
                        expected = 1
                        for heading, [number] in numbers:
                            if number != expected:
                                issues.append({
                                    "type": "discontinuous_number",
                                    "level": level,
                                    "expected": expected,
                                    "actual": number,
                                    "node_id": heading["id"],
                                    "title": heading.get("title", ""),
                                    "message": f"级别 {level} 的编号不连续，期望 {expected}，实际 {number}"
                                })
                                expected = number + 1
                            else:
                                expected += 1
                    
                    # 检查多级编号连续性（按级别分组检查）
                    else:
                        # 按父级编号分组
                        parent_groups = {}
                        for heading, number_parts in numbers:
                            parent_key = '.'.join(map(str, number_parts[:-1]))  # 父级编号
                            if parent_key not in parent_groups:
                                parent_groups[parent_key] = []
                            parent_groups[parent_key].append((heading, number_parts))
                        
                        # 检查每个父级组内的连续性
                        for parent_key, group_numbers in parent_groups.items():
                            group_numbers.sort(key=lambda x: x[1][-1])  # 按最后一级排序
                            expected = 1
                            for heading, number_parts in group_numbers:
                                current_number = number_parts[-1]
                                if current_number != expected:
                                    issues.append({
                                        "type": "discontinuous_number",
                                        "level": level,
                                        "expected": f"{parent_key}.{expected}" if parent_key else str(expected),
                                        "actual": '.'.join(map(str, number_parts)),
                                        "node_id": heading["id"],
                                        "title": heading.get("title", ""),
                                        "message": f"编号不连续，期望 {parent_key}.{expected}，实际 {'.'.join(map(str, number_parts))}"
                                    })
                                    expected = current_number + 1
                                else:
                                    expected += 1
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "total_headings": len(headings),
            "numbered_headings": sum(1 for h in headings if h.get("auto_number"))
        }
    
    def check_structure_integrity(self) -> Dict[str, Any]:
        """检查文档结构完整性"""
        issues = []
        
        # 检查孤立的节点（没有父节点但不是根节点）
        def check_orphaned_nodes(node: SIRNode, parent_id: Optional[str] = None):
            if parent_id is None and node["type"] != NodeType.DOCUMENT:
                issues.append({
                    "type": "orphaned_node",
                    "node_id": node["id"],
                    "node_type": node["type"],
                    "message": f"节点 {node['id']} ({node['type']}) 没有父节点"
                })
            
            for child in node.get("children", []):
                check_orphaned_nodes(child, node["id"])
        
        check_orphaned_nodes(self.editor.document["ast"])
        
        # 检查循环引用
        visited = set()
        
        def check_cycles(node: SIRNode):
            if node["id"] in visited:
                issues.append({
                    "type": "circular_reference",
                    "node_id": node["id"],
                    "node_type": node["type"],
                    "message": f"检测到循环引用: 节点 {node['id']}"
                })
                return
            
            visited.add(node["id"])
            for child in node.get("children", []):
                check_cycles(child)
            visited.remove(node["id"])
        
        check_cycles(self.editor.document["ast"])
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "total_nodes": len(visited)
        }
    
    def check_content_format(self) -> Dict[str, Any]:
        """检查内容格式一致性"""
        issues = []
        
        # 检查空内容
        def check_empty_content(node: SIRNode):
            if node["type"] in [NodeType.PARAGRAPH, NodeType.HEADING]:
                content = node.get("content", "")
                if not content or content.strip() == "":
                    issues.append({
                        "type": "empty_content",
                        "node_id": node["id"],
                        "node_type": node["type"],
                        "message": f"{node['type']} 节点 {node['id']} 内容为空"
                    })
            
            for child in node.get("children", []):
                check_empty_content(child)
        
        check_empty_content(self.editor.document["ast"])
        
        # 检查过长的行（代码块除外）
        def check_long_lines(node: SIRNode):
            if node["type"] in [NodeType.PARAGRAPH, NodeType.HEADING]:
                content = node.get("content", "")
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if len(line) > 120:  # 超过120字符的行
                        issues.append({
                            "type": "long_line",
                            "node_id": node["id"],
                            "node_type": node["type"],
                            "line_number": i + 1,
                            "length": len(line),
                            "message": f"{node['type']} 节点 {node['id']} 第{i+1}行过长 ({len(line)} 字符)"
                        })
            
            for child in node.get("children", []):
                check_long_lines(child)
        
        check_long_lines(self.editor.document["ast"])
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues
        }
    
    def check_link_integrity(self) -> Dict[str, Any]:
        """检查链接完整性"""
        issues = []
        
        # 提取所有链接
        def extract_links(node: SIRNode):
            content = node.get("content", "") or ""
            # 简单的链接提取（实际实现应该更复杂）
            link_patterns = [
                r'\[(.*?)\]\((.*?)\)',  # Markdown 链接
                r'(https?:\/\/[^\s]+)',   # 裸URL
            ]
            
            links = []
            for pattern in link_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    if pattern == r'\[(.*?)\]\((.*?)\)':
                        link_text, url = match.groups()
                    else:
                        url = match.group(1)
                        link_text = url
                    
                    links.append({
                        "url": url,
                        "text": link_text,
                        "node_id": node["id"],
                        "node_type": node["type"]
                    })
            
            return links
        
        def check_links_in_node(node: SIRNode):
            links = extract_links(node)
            for link in links:
                # 检查空链接
                if not link["url"] or link["url"].strip() == "":
                    issues.append({
                        "type": "empty_link",
                        "node_id": node["id"],
                        "link_text": link["text"],
                        "message": f"空链接: {link['text']}"
                    })
                
                # 检查自引用链接（TODO: 需要更复杂的实现）
                if link["url"].startswith('#'):
                    anchor = link["url"][1:]
                    # 检查锚点是否存在（简化实现）
                    headings = self.editor._find_nodes_by_type(NodeType.HEADING)
                    anchor_exists = any(h.get("anchor") == anchor for h in headings)
                    if not anchor_exists:
                        issues.append({
                            "type": "broken_anchor",
                            "node_id": node["id"],
                            "anchor": anchor,
                            "message": f"锚点链接 #{anchor} 不存在"
                        })
            
            for child in node.get("children", []):
                check_links_in_node(child)
        
        check_links_in_node(self.editor.document["ast"])
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "total_links": len(issues)  # 简化统计
        }
    
    def check_metadata_completeness(self) -> Dict[str, Any]:
        """检查元数据完整性"""
        issues = []
        metadata = self.editor.document.get("metadata", {})
        
        # 检查必要元数据字段
        required_fields = ["title", "author", "created_date"]
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues.append({
                    "type": "missing_metadata",
                    "field": field,
                    "message": f"缺少必要的元数据字段: {field}"
                })
        
        # 检查日期格式
        if "created_date" in metadata:
            date_str = metadata["created_date"]
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                issues.append({
                    "type": "invalid_date_format",
                    "field": "created_date",
                    "value": date_str,
                    "message": f"日期格式不正确，期望 YYYY-MM-DD，实际: {date_str}"
                })
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "total_metadata_fields": len(metadata)
        }


class AutoRepair:
    """自动修复器 - 提供基于一致性检查结果的自动修复功能"""
    
    def __init__(self, editor: SemanticEditor):
        self.editor = editor
        self.checker = ConsistencyChecker(editor)
    
    def repair_all(self) -> Dict[str, Any]:
        """执行所有可用的自动修复"""
        check_results = self.checker.check_all()
        repair_results = {}
        
        # 按类别修复
        for check_name, result in check_results.items():
            if result["has_issues"]:
                repair_method = getattr(self, f"repair_{check_name}", None)
                if repair_method:
                    repair_results[check_name] = repair_method(result["issues"])
        
        return {
            "check_results": check_results,
            "repair_results": repair_results,
            "total_fixed": sum(len(r.get("fixed", [])) for r in repair_results.values())
        }
    
    def repair_heading_numbering(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """修复标题编号问题"""
        fixed = []
        not_fixed = []
        
        for issue in issues:
            if issue["type"] == "duplicate_number":
                # 重新编号所有标题
                result = self.editor.renumber_headings()
                if result.success:
                    fixed.append(issue)
                else:
                    not_fixed.append(issue)
                break  # 重新编号会修复所有编号问题
            elif issue["type"] == "discontinuous_number":
                # 重新编号所有标题
                result = self.editor.renumber_headings()
                if result.success:
                    fixed.append(issue)
                else:
                    not_fixed.append(issue)
                break  # 重新编号会修复所有编号问题
        
        return {
            "fixed": fixed,
            "not_fixed": not_fixed,
            "total_issues": len(issues)
        }
    
    def repair_structure_integrity(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """修复结构完整性问题"""
        fixed = []
        not_fixed = []
        
        for issue in issues:
            if issue["type"] == "orphaned_node":
                # 将孤立节点附加到根节点
                node = self.editor._find_node_by_id(issue["node_id"])
                if node:
                    root = self.editor.document["ast"]
                    if "children" not in root:
                        root["children"] = []
                    root["children"].append(node)
                    fixed.append(issue)
                else:
                    not_fixed.append(issue)
            elif issue["type"] == "circular_reference":
                # 循环引用需要手动修复
                not_fixed.append(issue)
        
        return {
            "fixed": fixed,
            "not_fixed": not_fixed,
            "total_issues": len(issues)
        }
    
    def repair_content_format(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """修复内容格式问题"""
        fixed = []
        not_fixed = []
        
        for issue in issues:
            if issue["type"] == "empty_content":
                # 为空的段落或标题添加默认内容
                node = self.editor._find_node_by_id(issue["node_id"])
                if node:
                    if node["type"] == NodeType.PARAGRAPH:
                        node["content"] = "待补充内容"
                        fixed.append(issue)
                    elif node["type"] == NodeType.HEADING:
                        node["content"] = "待补充标题"
                        node["title"] = "待补充标题"
                        fixed.append(issue)
                else:
                    not_fixed.append(issue)
            elif issue["type"] == "long_line":
                # 长行需要手动修复
                not_fixed.append(issue)
        
        return {
            "fixed": fixed,
            "not_fixed": not_fixed,
            "total_issues": len(issues)
        }
    
    def repair_link_integrity(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """修复链接完整性问题"""
        fixed = []
        not_fixed = []
        
        for issue in issues:
            if issue["type"] == "empty_link":
                # 移除空链接
                node = self.editor._find_node_by_id(issue["node_id"])
                if node:
                    # 简化实现：移除链接语法
                    content = node.get("content", "")
                    content = re.sub(r'\[.*?\]\(\)', '', content)  # 移除空链接
                    node["content"] = content
                    fixed.append(issue)
                else:
                    not_fixed.append(issue)
            elif issue["type"] == "broken_anchor":
                # 损坏的锚点需要手动修复
                not_fixed.append(issue)
        
        return {
            "fixed": fixed,
            "not_fixed": not_fixed,
            "total_issues": len(issues)
        }
    
    def repair_metadata_completeness(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """修复元数据完整性问题"""
        fixed = []
        not_fixed = []
        
        metadata = self.editor.document.get("metadata", {})
        
        for issue in issues:
            if issue["type"] == "missing_metadata":
                field = issue["field"]
                if field == "title":
                    metadata["title"] = "未命名文档"
                    fixed.append(issue)
                elif field == "author":
                    metadata["author"] = "未知作者"
                    fixed.append(issue)
                elif field == "created_date":
                    metadata["created_date"] = "2024-01-01"
                    fixed.append(issue)
            elif issue["type"] == "invalid_date_format":
                # 日期格式需要手动修复
                not_fixed.append(issue)
        
        # 确保metadata存在
        self.editor.document["metadata"] = metadata
        
        return {
            "fixed": fixed,
            "not_fixed": not_fixed,
            "total_issues": len(issues)
        }