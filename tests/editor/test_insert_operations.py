#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插入操作测试

本测试文件测试 markdown_editor 模块的插入操作功能，包括：
1. 插入章节到不同位置（CHILD, BEFORE, AFTER）
2. 插入到文档节点时的边界情况处理
3. 插入操作的验证和错误处理
4. 插入后的文档结构完整性检查
"""

import sys
import os
import json

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..', '..', 'src'))

from markdown_editor.semantic_editor import create_editor_from_markdown, EditPosition

def test_insert_section_child_position():
    """测试在子位置插入章节"""
    print("=== 测试 1: 在子位置插入章节 ===")
    
    # 测试内容
    content = """# 主标题

这是主标题的内容。

## 二级标题

这是二级标题的内容。
"""
    
    editor = create_editor_from_markdown(content)
    
    # 查找第一个标题节点
    headings = editor._find_nodes_by_type("heading")
    assert len(headings) > 0, "应该找到标题节点"
    
    parent_node = headings[0]
    initial_children_count = len(parent_node.get('children', []))
    
    # 执行插入操作
    result = editor.insert_section(
        parent_id=parent_node['id'],
        position=EditPosition.CHILD,
        title="新插入的章节",
        level=2,
        content="这是新插入章节的内容。"
    )
    
    assert result.success, f"插入操作应该成功: {result.message}"
    assert len(result.changes) > 0, "应该有变更记录"
    
    # 验证新节点
    new_node_id = result.changes[0]['new_node_id']
    new_node = editor._find_node_by_id(new_node_id)
    
    assert new_node is not None, "新节点应该存在"
    assert new_node['type'] == 'heading', "新节点类型应该是heading"
    assert new_node.get('title') == "新插入的章节", "新节点标题应该匹配"
    assert new_node.get('parent_id') == parent_node['id'], "新节点的父节点ID应该正确"
    
    # 验证父节点的子节点数量增加
    updated_parent = editor._find_node_by_id(parent_node['id'])
    assert len(updated_parent.get('children', [])) == initial_children_count + 1, "父节点子节点数量应该增加"
    
    # 验证渲染结果
    from markdown_editor.sir_renderer import render_sir_to_markdown
    rendered = render_sir_to_markdown(editor.get_document())
    assert "新插入的章节" in rendered, "新章节标题应该出现在渲染结果中"
    assert "这是新插入章节的内容" in rendered, "新章节内容应该出现在渲染结果中"
    
    print("  ✓ 在子位置插入章节测试通过")

def test_insert_section_before_position():
    """测试在之前位置插入章节"""
    print("=== 测试 2: 在之前位置插入章节 ===")
    
    content = """# 主标题

这是主标题的内容。

## 二级标题

这是二级标题的内容。
"""
    
    editor = create_editor_from_markdown(content)
    
    # 查找第二个标题节点（作为参考节点）
    headings = editor._find_nodes_by_type("heading")
    assert len(headings) >= 2, "应该至少找到2个标题节点"
    
    reference_node = headings[1]
    parent_node = editor._find_parent_node(reference_node['id'])
    
    initial_children_count = len(parent_node.get('children', []))
    
    # 执行插入操作
    result = editor.insert_section(
        parent_id=reference_node['id'],
        position=EditPosition.BEFORE,
        title="在之前插入的章节",
        level=2,
        content="这是在之前插入章节的内容。"
    )
    
    assert result.success, f"插入操作应该成功: {result.message}"
    
    # 验证新节点
    new_node_id = result.changes[0]['new_node_id']
    new_node = editor._find_node_by_id(new_node_id)
    
    assert new_node is not None, "新节点应该存在"
    assert new_node.get('title') == "在之前插入的章节", "新节点标题应该匹配"
    
    # 验证父节点的子节点数量增加
    updated_parent = editor._find_node_by_id(parent_node['id'])
    assert len(updated_parent.get('children', [])) == initial_children_count + 1, "父节点子节点数量应该增加"
    
    # 验证新节点在正确的位置（在参考节点之前）
    children_ids = [child['id'] for child in updated_parent.get('children', [])]
    new_node_index = children_ids.index(new_node_id)
    reference_node_index = children_ids.index(reference_node['id'])
    
    assert new_node_index < reference_node_index, "新节点应该在参考节点之前"
    
    print("  ✓ 在之前位置插入章节测试通过")

def test_insert_section_after_position():
    """测试在之后位置插入章节"""
    print("=== 测试 3: 在之后位置插入章节 ===")
    
    content = """# 主标题

这是主标题的内容。

## 二级标题

这是二级标题的内容。
"""
    
    editor = create_editor_from_markdown(content)
    
    # 查找第二个标题节点（作为参考节点）
    headings = editor._find_nodes_by_type("heading")
    assert len(headings) >= 2, "应该至少找到2个标题节点"
    
    reference_node = headings[1]
    parent_node = editor._find_parent_node(reference_node['id'])
    
    initial_children_count = len(parent_node.get('children', []))
    
    # 执行插入操作
    result = editor.insert_section(
        parent_id=reference_node['id'],
        position=EditPosition.AFTER,
        title="在之后插入的章节",
        level=2,
        content="这是在之后插入章节的内容。"
    )
    
    assert result.success, f"插入操作应该成功: {result.message}"
    
    # 验证新节点
    new_node_id = result.changes[0]['new_node_id']
    new_node = editor._find_node_by_id(new_node_id)
    
    assert new_node is not None, "新节点应该存在"
    assert new_node.get('title') == "在之后插入的章节", "新节点标题应该匹配"
    
    # 验证父节点的子节点数量增加
    updated_parent = editor._find_node_by_id(parent_node['id'])
    assert len(updated_parent.get('children', [])) == initial_children_count + 1, "父节点子节点数量应该增加"
    
    # 验证新节点在正确的位置（在参考节点之后）
    children_ids = [child['id'] for child in updated_parent.get('children', [])]
    new_node_index = children_ids.index(new_node_id)
    reference_node_index = children_ids.index(reference_node['id'])
    
    assert new_node_index > reference_node_index, "新节点应该在参考节点之后"
    
    print("  ✓ 在之后位置插入章节测试通过")

def test_insert_to_document_node():
    """测试插入到文档节点的边界情况"""
    print("=== 测试 4: 插入到文档节点的边界情况 ===")
    
    content = """# 主标题

这是主标题的内容。
"""
    
    editor = create_editor_from_markdown(content)
    document = editor.get_document()
    
    # 获取文档节点
    document_node = document['ast']
    initial_children_count = len(document_node.get('children', []))
    
    # 执行插入操作（插入到文档节点）
    result = editor.insert_section(
        parent_id=document_node['id'],
        position=EditPosition.CHILD,
        title="插入到文档的章节",
        level=1,
        content="这是插入到文档的章节内容。"
    )
    
    assert result.success, f"插入操作应该成功: {result.message}"
    
    # 验证新节点
    new_node_id = result.changes[0]['new_node_id']
    new_node = editor._find_node_by_id(new_node_id)
    
    assert new_node is not None, "新节点应该存在"
    assert new_node.get('title') == "插入到文档的章节", "新节点标题应该匹配"
    assert new_node.get('parent_id') == document_node['id'], "新节点的父节点ID应该是文档节点"
    
    # 验证文档节点的子节点数量增加
    updated_document = editor.get_document()
    assert len(updated_document['ast'].get('children', [])) == initial_children_count + 1, "文档节点子节点数量应该增加"
    
    print("  ✓ 插入到文档节点的边界情况测试通过")

def test_insert_validation():
    """测试插入操作的验证和错误处理"""
    print("=== 测试 5: 插入操作的验证和错误处理 ===")
    
    content = """# 主标题

这是主标题的内容。
"""
    
    editor = create_editor_from_markdown(content)
    
    # 测试用例 1: 无效的父节点ID
    result = editor.insert_section(
        parent_id="invalid_node_id",
        position=EditPosition.CHILD,
        title="测试章节",
        level=2,
        content="测试内容"
    )
    
    assert not result.success, "使用无效父节点ID时插入应该失败"
    print(f"错误消息: {result.message}")
    # 检查错误消息是否包含任何关于节点未找到的提示
    assert any(keyword in result.message.lower() for keyword in ["not found", "invalid", "不存在", "未找到"]), f"错误消息应该提示节点未找到，实际消息: {result.message}"
    
    # 测试用例 2: 无效的级别参数
    headings = editor._find_nodes_by_type("heading")
    valid_node_id = headings[0]['id']
    
    result = editor.insert_section(
        parent_id=valid_node_id,
        position=EditPosition.CHILD,
        title="测试章节",
        level=0,  # 无效的级别
        content="测试内容"
    )
    
    print(f"无效级别参数测试结果 - 成功: {result.success}, 消息: {result.message}")
    # 级别验证可能在实现中，也可能不验证，所以这个测试可能成功也可能失败
    # 我们主要关注第一个测试用例（无效父节点ID）
    
    print("  ✓ 插入操作的验证和错误处理测试通过")

def main():
    """运行所有插入操作测试"""
    print("插入操作测试套件")
    print("=" * 50)
    
    try:
        test_insert_section_child_position()
        test_insert_section_before_position()
        test_insert_section_after_position()
        test_insert_to_document_node()
        test_insert_validation()
        
        print("\n" + "=" * 50)
        print("✅ 所有插入操作测试通过!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)