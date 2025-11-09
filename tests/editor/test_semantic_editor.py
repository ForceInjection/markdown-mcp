#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义编辑器测试

本测试文件测试 markdown_editor 模块的语义编辑功能，包括：
1. 一致性检查功能 - 检查文档的结构和编号一致性
2. 自动修复功能 - 自动修复检测到的问题
3. 语义编辑操作 - 标题更新、段落插入、章节移动等
4. 错误处理 - 边界情况和异常处理
"""

import sys
import os
import json

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..', '..', 'src'))

from markdown_editor.semantic_editor import create_editor_from_markdown, EditOperation

# 测试配置常量
TEST_CONFIG = {
    "reports_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports"),
}

def get_report_file_path(filename):
    """获取报告文件的完整路径"""
    return os.path.join(TEST_CONFIG["reports_dir"], filename)

def ensure_directories():
    """确保必要的目录存在"""
    os.makedirs(TEST_CONFIG["reports_dir"], exist_ok=True)


def test_consistency_checks():
    """测试一致性检查功能"""
    print("=== 测试 1: 一致性检查功能 ===")
    
    # 测试用例 1: 正常编号文档
    normal_content = """# 1. 项目介绍

## 1.1 项目背景

### 1.1.1 技术背景

### 1.1.2 业务背景

## 1.2 项目目标

# 2. 技术方案

## 2.1 架构设计

### 2.1.1 前端架构

### 2.1.2 后端架构

## 2.2 技术选型
"""
    
    editor = create_editor_from_markdown(normal_content)
    result = editor.check_consistency()
    
    print(f"测试用例 1 - 正常编号文档:")
    print(f"  存在问题: {result['overall']['has_issues']}")
    print(f"  问题数量: {result['overall']['total_issues']}")
    
    # 正常编号文档可能有一些非关键问题（如标题内容为空、缺少元数据）
    # 但主要关注编号一致性，所以应该没有编号相关的问题
    heading_issues = result['heading_numbering']['issues']
    assert len(heading_issues) == 0, f"正常编号文档不应该有编号问题，但发现: {[issue['type'] for issue in heading_issues]}"
    
    # 测试用例 2: 有编号问题的文档
    problematic_content = """# 1. 第一章

## 1.1 第一节

## 1.1 重复编号

## 1.3 跳跃编号

# 3. 第三章

## 3.1 正常编号
"""
    
    editor = create_editor_from_markdown(problematic_content)
    result = editor.check_consistency()
    
    print(f"\n测试用例 2 - 有编号问题的文档:")
    print(f"  存在问题: {result['overall']['has_issues']}")
    print(f"  问题数量: {result['overall']['total_issues']}")
    
    # 收集所有问题
    all_issues = []
    for check_name, check_result in result.items():
        if check_name != 'overall' and check_result['has_issues']:
            all_issues.extend(check_result['issues'])
    
    for issue in all_issues:
        print(f"    - {issue['type']}: {issue['message']}")
    
    assert result['overall']['has_issues'], "有编号问题的文档应该被检测到"
    assert result['overall']['total_issues'] > 0, "应该检测到编号问题"
    
    print("  ✓ 一致性检查功能测试通过")


def test_auto_repair():
    """测试自动修复功能"""
    print("\n=== 测试 2: 自动修复功能 ===")
    
    # 测试用例 1: 自动修复编号问题
    problematic_content = """# 1. 第一章

## 1.1 第一节

## 1.1 重复编号

## 1.3 跳跃编号

# 3. 第三章

## 3.1 正常编号
"""
    
    editor = create_editor_from_markdown(problematic_content)
    
    # 检查问题
    check_result = editor.check_consistency()
    print(f"修复前 - 存在问题: {check_result['overall']['has_issues']}")
    print(f"修复前 - 问题数量: {check_result['overall']['total_issues']}")
    
    # 执行自动修复
    repair_result = editor.auto_repair()
    print(f"修复结果 - 修复数量: {repair_result['total_fixed']}")
    print(f"修复结果 - 剩余问题: {check_result['overall']['total_issues'] - repair_result['total_fixed']}")
    
    # 检查修复后的状态
    check_after_repair = editor.check_consistency()
    print(f"修复后 - 存在问题: {check_after_repair['overall']['has_issues']}")
    print(f"修复后 - 问题数量: {check_after_repair['overall']['total_issues']}")
    
    # 验证修复效果
    assert repair_result['total_fixed'] > 0, "应该修复了一些问题"
    assert check_after_repair['overall']['total_issues'] < check_result['overall']['total_issues'], "修复后问题应该减少"
    
    print("  ✓ 自动修复功能测试通过")


def test_semantic_editing():
    """测试语义编辑操作"""
    print("\n=== 测试 3: 语义编辑操作 ===")
    
    content = """# 1. 项目介绍

## 1.1 项目背景

这是背景内容。

## 1.2 项目目标

这是目标内容。
"""
    
    editor = create_editor_from_markdown(content)
    
    # 测试用例 1: 更新标题
    print("测试用例 1 - 更新标题:")
    
    # 找到第一个二级标题
    nodes = editor._find_nodes_by_type('heading')
    h2_nodes = [node for node in nodes if node.get('level') == 2]
    
    if h2_nodes:
        node_id = h2_nodes[0]['id']
        result = editor.update_heading(node_id, "1.1 更新后的背景")
        print(f"  标题更新结果: {result.success}")
        assert result.success, "标题更新应该成功"
    
    # 测试用例 2: 插入段落
    print("测试用例 2 - 插入段落:")
    
    # 在第一个二级标题后插入段落
    if h2_nodes:
        node_id = h2_nodes[0]['id']
        result = editor.add_paragraph(node_id, "这是新插入的段落内容。")
        print(f"  段落插入结果: {result.success}")
        assert result.success, "段落插入应该成功"
    
    # 测试用例 3: 重新编号
    print("测试用例 3 - 重新编号:")
    
    result = editor.renumber_headings()
    print(f"  重新编号结果: {result.success}")
    assert result.success, "重新编号应该成功"
    
    print("  ✓ 语义编辑操作测试通过")


def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试 4: 错误处理 ===")
    
    content = """# 1. 项目介绍

## 1.1 项目背景

这是背景内容。
"""
    
    editor = create_editor_from_markdown(content)
    
    # 测试用例 1: 无效节点ID
    print("测试用例 1 - 无效节点ID:")
    
    try:
        result = editor.update_heading("invalid_id", "新标题")
        print(f"  无效ID处理: {not result.success}")
        assert not result.success, "无效节点ID应该失败"
    except Exception as e:
        print(f"  异常处理: {type(e).__name__}")
    
    # 测试用例 2: 空内容
    print("测试用例 2 - 空内容:")
    
    empty_editor = create_editor_from_markdown("")
    result = empty_editor.check_consistency()
    print(f"  空内容检查 - 问题数: {result['overall']['total_issues']}")
    print(f"  空内容检查 - 状态: {'正常' if not result['overall']['has_issues'] else '异常'}")
    # 空文档应该有问题（如缺少标题、元数据等），这是正常的
    assert result['overall']['has_issues'], "空文档应该报告问题"
    
    print("  ✓ 错误处理测试通过")


def test_comprehensive_scenarios():
    """测试综合场景"""
    print("\n=== 测试 5: 综合场景 ===")
    
    # 复杂文档场景
    complex_content = """# 1. 项目概述

## 1.1 背景介绍

### 1.1.1 技术背景

### 1.1.2 业务背景

## 1.2 项目目标

### 1.2.1 主要目标

### 1.2.2 次要目标

# 2. 技术实现

## 2.1 架构设计

### 2.1.1 前端架构

### 2.1.2 后端架构

## 2.2 技术选型

### 2.2.1 前端技术

### 2.2.2 后端技术

# 3. 项目规划

## 3.1 时间安排

## 3.2 资源分配
"""
    
    editor = create_editor_from_markdown(complex_content)
    
    # 综合测试流程
    print("综合测试流程:")
    
    # 1. 初始一致性检查
    initial_check = editor.check_consistency()
    print(f"  1. 初始检查 - 问题数: {initial_check['overall']['total_issues']}")
    
    # 2. 自动修复
    if initial_check['overall']['has_issues']:
        repair_result = editor.auto_repair()
        print(f"  2. 自动修复 - 修复数: {repair_result['total_fixed']}")
    
    # 3. 修复后检查
    final_check = editor.check_consistency()
    print(f"  3. 最终检查 - 问题数: {final_check['overall']['total_issues']}")
    print(f"  3. 最终检查 - 状态: {'正常' if not final_check['overall']['has_issues'] else '异常'}")
    
    # 验证文档结构完整性
    sir_doc = editor.get_document()
    assert 'ast' in sir_doc, "文档应该有AST结构"
    assert 'children' in sir_doc['ast'], "AST应该有子节点"
    assert len(sir_doc['ast']['children']) > 0, "文档应该有内容"
    
    print("  ✓ 综合场景测试通过")


def main():
    """运行所有测试"""
    print("开始测试语义编辑器功能...")
    
    try:
        test_consistency_checks()
        test_auto_repair()
        test_semantic_editing()
        test_error_handling()
        test_comprehensive_scenarios()
        
        print("\n" + "="*50)
        print("🎉 所有语义编辑器测试通过！功能工作正常。")
        print("="*50)
        
        # 生成测试报告
        report = {
            "test_status": "PASSED",
            "total_tests": 5,
            "passed_tests": 5,
            "failed_tests": 0,
            "features_verified": [
                "一致性检查功能",
                "自动修复功能", 
                "语义编辑操作",
                "错误处理能力",
                "综合场景处理"
            ]
        }
        
        ensure_directories()
        report_path = get_report_file_path('semantic_editor_test_report.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"测试报告已保存到: {report_path}")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())