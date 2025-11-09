#!/usr/bin/env python3
"""
测试脚本：针对 Apache Spark 复杂文档进行语义分析测试
"""

import sys
import os
import json

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..', '..', 'src'))

from markdown_editor.semantic_editor import SemanticEditor, create_editor_from_markdown
from markdown_editor.sir_renderer import render_sir_to_markdown

def test_apache_spark_document():
    """测试 Apache Spark 复杂文档的语义分析"""
    
    # 读取 Apache Spark 文档内容
    spark_doc_path = os.path.join('tests', 'fixtures', 'Apache Spark 设计与实现.md')
    
    try:
        with open(spark_doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"文档大小: {len(content)} 字符")
        print(f"文档行数: {len(content.split('\n'))} 行")
        
        # 创建语义编辑器实例
        editor = create_editor_from_markdown(content)
        
        # 执行语义分析
        print("\n=== 执行语义分析 ===")
        analysis_result = editor.check_consistency()
        
        print(f"初始问题数量: {len(analysis_result.get('issues', []))}")
        print(f"总体状态: {analysis_result.get('overall', {}).get('status', 'unknown')}")
        
        # 显示前10个问题（如果有）
        issues = analysis_result.get('issues', [])
        if issues:
            print(f"\n=== 前10个问题 ===")
            for i, issue in enumerate(issues[:10], 1):
                print(f"{i}. [{issue.get('type', 'unknown')}] {issue.get('message', 'No message')}")
                print(f"   位置: {issue.get('location', 'unknown')}")
        
        # 执行自动修复
        print("\n=== 执行自动修复 ===")
        repair_result = editor.auto_repair()
        
        print(f"修复操作数量: {len(repair_result.get('operations', []))}")
        print(f"修复后问题数量: {len(repair_result.get('remaining_issues', []))}")
        
        # 检查修复后的文档状态
        print("\n=== 检查修复后状态 ===")
        final_check = editor.check_consistency()
        print(f"最终问题数量: {len(final_check.get('issues', []))}")
        print(f"最终状态: {final_check.get('overall', {}).get('status', 'unknown')}")
        
        # 获取修复后的文档并转换为 Markdown
        repaired_sir_doc = editor.get_document()
        repaired_markdown = render_sir_to_markdown(repaired_sir_doc)
        print(f"修复后文档大小: {len(repaired_markdown)} 字符")
        
        # 保存修复后的文档（可选）
        repaired_path = os.path.join('tests', 'fixtures', 'Apache Spark 设计与实现_REPAIRED.md')
        with open(repaired_path, 'w', encoding='utf-8') as f:
            f.write(repaired_markdown)
        
        print(f"修复后文档已保存到: {repaired_path}")
        
        return {
            'original_size': len(content),
            'repaired_size': len(repaired_markdown),
            'initial_issues': len(analysis_result.get('issues', [])),
            'remaining_issues': len(final_check.get('issues', [])),
            'repair_operations': len(repair_result.get('operations', [])),
            'status': final_check.get('overall', {}).get('status', 'unknown')
        }
        
    except FileNotFoundError:
        print(f"错误: 找不到文档文件 {spark_doc_path}")
        return None
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_document_structure():
    """分析文档结构"""
    
    spark_doc_path = os.path.join('tests', 'fixtures', 'Apache Spark 设计与实现.md')
    
    try:
        with open(spark_doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 统计各级标题数量
        heading_counts = {'#': 0, '##': 0, '###': 0, '####': 0, '#####': 0, '######': 0}
        code_blocks = 0
        tables = 0
        lists = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # 统计标题
            if line_stripped.startswith('#'):
                level = line_stripped.split(' ')[0].count('#')
                if level <= 6:
                    heading_counts['#' * level] += 1
            
            # 统计代码块
            if line_stripped.startswith('```'):
                code_blocks += 1
            
            # 统计表格（简单检测）
            if '|' in line_stripped and len(line_stripped.split('|')) >= 3:
                tables += 1
            
            # 统计列表项
            if line_stripped.startswith(('- ', '* ', '+ ', '1. ', '2. ', '3. ')):
                lists += 1
        
        print("\n=== 文档结构分析 ===")
        print(f"总行数: {len(lines)}")
        print(f"一级标题 (#): {heading_counts['#']}")
        print(f"二级标题 (##): {heading_counts['##']}")
        print(f"三级标题 (###): {heading_counts['###']}")
        print(f"四级标题 (####): {heading_counts['####']}")
        print(f"五级标题 (#####): {heading_counts['#####']}")
        print(f"六级标题 (######): {heading_counts['######']}")
        print(f"代码块数量: {code_blocks // 2} (约)")  # 每个代码块有开始和结束
        print(f"表格数量: {tables}")
        print(f"列表项数量: {lists}")
        
    except Exception as e:
        print(f"结构分析错误: {e}")

if __name__ == "__main__":
    print("开始测试 Apache Spark 复杂文档语义分析...")
    
    # 分析文档结构
    analyze_document_structure()
    
    # 执行语义分析测试
    result = test_apache_spark_document()
    
    if result:
        print("\n=== 测试结果汇总 ===")
        print(f"原始文档大小: {result['original_size']} 字符")
        print(f"修复后文档大小: {result['repaired_size']} 字符")
        print(f"初始问题数量: {result['initial_issues']}")
        print(f"修复操作数量: {result['repair_operations']}")
        print(f"剩余问题数量: {result['remaining_issues']}")
        print(f"最终状态: {result['status']}")
    else:
        print("测试失败")