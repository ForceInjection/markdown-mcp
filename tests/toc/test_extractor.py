#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown TOC 核心功能测试

本测试文件测试 MarkdownTOCExtractor 的核心功能，包括：
1. TOC 提取功能 - 各种 Markdown 格式的标题提取
2. 编号问题分析功能 - 重复编号和不连续编号检测
3. TOC 生成功能 - 多种格式的 TOC 生成
4. 汉字编号识别功能 - 中文数字的识别和转换
5. 便利函数测试 - 一体化接口函数验证
6. has_issues 含义测试 - 编号问题状态验证
"""

import json
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from markdown_toc.extractor import MarkdownTOCExtractor, extract_toc_from_content, analyze_numbering_issues_from_headers, generate_toc_from_headers

# 动态导入 test_config，支持作为模块和独立脚本运行
try:
    from ..test_config import TEST_CONFIG, get_report_file_path, ensure_directories
except ImportError:
    # 作为独立脚本运行时，使用绝对导入
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from test_config import TEST_CONFIG, get_report_file_path, ensure_directories


def test_toc_extraction():
    """测试 TOC 提取功能"""
    print("=== 测试 1: TOC 提取功能 ===")
    
    # 测试用例 1: 基本标题提取
    content1 = """# 第一章 介绍
这是介绍内容。

## 1.1 背景
背景内容。

### 1.1.1 历史
历史内容。

## 1.2 目标
目标内容。

# 第二章 方法
方法内容。

```python
# 这是代码块中的注释，不应该被提取
def example():
    pass
```

## 2.1 实现
实现内容。
"""
    
    extractor = MarkdownTOCExtractor()
    headers1 = extractor.extract_toc(content1)
    
    print(f"测试用例 1 - 基本标题提取:")
    print(f"  提取到 {len(headers1)} 个标题:")
    for header in headers1:
        print(f"    L{header['level']}: {header['title']} (第 {header['line_number']} 行)")
    
    # 验证结果
    expected_titles = ["第一章 介绍", "1.1 背景", "1.1.1 历史", "1.2 目标", "第二章 方法", "2.1 实现"]
    actual_titles = [h['title'] for h in headers1]
    assert actual_titles == expected_titles, f"标题提取错误: 期望 {expected_titles}, 实际 {actual_titles}"
    
    # 测试用例 2: 包含特殊字符的标题
    content2 = "# **粗体标题**\n## *斜体标题*\n### `代码标题`\n#### [链接标题](http://example.com)\n##### 混合 **粗体** 和 *斜体* 的标题\n"
    
    headers2 = extractor.extract_toc(content2)
    print(f"\n测试用例 2 - 特殊字符标题:")
    print(f"  提取到 {len(headers2)} 个标题:")
    for header in headers2:
        print(f"    L{header['level']}: {header['title']}")
    
    # 验证清理后的标题
    expected_clean_titles = ["粗体标题", "斜体标题", "代码标题", "链接标题", "混合 粗体 和 斜体 的标题"]
    actual_clean_titles = [h['title'] for h in headers2]
    assert actual_clean_titles == expected_clean_titles, f"标题清理错误: 期望 {expected_clean_titles}, 实际 {actual_clean_titles}"
    
    print("  ✓ TOC 提取功能测试通过")


def test_numbering_analysis():
    """测试编号问题分析功能"""
    print("\n=== 测试 2: 编号问题分析功能 ===")
    
    # 测试用例 1: 正常编号
    normal_headers = [
        {'level': 1, 'title': '1. 介绍', 'line_number': 1},
        {'level': 1, 'title': '2. 方法', 'line_number': 5},
        {'level': 1, 'title': '3. 结果', 'line_number': 10},
        {'level': 2, 'title': '3.1 数据', 'line_number': 12},
        {'level': 2, 'title': '3.2 分析', 'line_number': 15}
    ]
    
    extractor = MarkdownTOCExtractor()
    result1 = extractor.analyze_numbering_issues(normal_headers)
    
    print(f"测试用例 1 - 正常编号:")
    print(f"  存在问题: {result1['has_issues']}")
    print(f"  重复编号: {len(result1['duplicate_numbers'])} 个")
    print(f"  不连续编号: {len(result1['discontinuous_numbers'])} 个")
    
    assert not result1['has_issues'], "正常编号不应该有问题"
    
    # 测试用例 2: 重复编号
    duplicate_headers = [
        {'level': 1, 'title': '1. 介绍', 'line_number': 1},
        {'level': 1, 'title': '2. 方法', 'line_number': 5},
        {'level': 1, 'title': '1. 重复', 'line_number': 10},  # 重复编号
        {'level': 2, 'title': '2.1 子章节', 'line_number': 12},
        {'level': 2, 'title': '2.1 重复子章节', 'line_number': 15}  # 重复编号
    ]
    
    result2 = extractor.analyze_numbering_issues(duplicate_headers)
    
    print(f"\n测试用例 2 - 重复编号:")
    print(f"  存在问题: {result2['has_issues']}")
    print(f"  重复编号: {len(result2['duplicate_numbers'])} 个")
    for dup in result2['duplicate_numbers']:
        print(f"    级别 {dup['level']}, 编号 {dup['number']}: {len(dup['occurrences'])} 次出现")
    
    assert result2['has_issues'], "重复编号应该被检测到"
    assert len(result2['duplicate_numbers']) == 2, f"应该检测到 2 个重复编号，实际 {len(result2['duplicate_numbers'])}"
    
    # 测试用例 3: 不连续编号
    discontinuous_headers = [
        {'level': 1, 'title': '1. 介绍', 'line_number': 1},
        {'level': 1, 'title': '3. 跳过了2', 'line_number': 5},  # 跳过了 2
        {'level': 1, 'title': '4. 正常', 'line_number': 10},
        {'level': 2, 'title': '4.1 子章节', 'line_number': 12},
        {'level': 2, 'title': '4.3 跳过了4.2', 'line_number': 15}  # 跳过了 4.2
    ]
    
    result3 = extractor.analyze_numbering_issues(discontinuous_headers)
    
    print(f"\n测试用例 3 - 不连续编号:")
    print(f"  存在问题: {result3['has_issues']}")
    print(f"  不连续编号: {len(result3['discontinuous_numbers'])} 个")
    for disc in result3['discontinuous_numbers']:
        print(f"    级别 {disc['level']}, 期望 {disc['expected']}, 实际 {disc['actual']} (第 {disc['line_number']} 行)")
    
    assert result3['has_issues'], "不连续编号应该被检测到"
    assert len(result3['discontinuous_numbers']) == 2, f"应该检测到 2 个不连续编号，实际 {len(result3['discontinuous_numbers'])}"
    
    print("  ✓ 编号问题分析功能测试通过")


def test_toc_generation():
    """测试 TOC 生成功能"""
    print("\n=== 测试 3: TOC 生成功能 ===")
    
    # 测试数据
    test_headers = [
        {'level': 1, 'title': '介绍', 'line_number': 1},
        {'level': 2, 'title': '背景', 'line_number': 3},
        {'level': 2, 'title': '目标', 'line_number': 8},
        {'level': 1, 'title': '方法', 'line_number': 12},
        {'level': 2, 'title': '数据收集', 'line_number': 15},
        {'level': 3, 'title': '样本选择', 'line_number': 18},
        {'level': 2, 'title': '数据分析', 'line_number': 22}
    ]
    
    extractor = MarkdownTOCExtractor()
    
    # 测试用例 1: Markdown 格式（无链接）
    result1 = extractor.generate_toc(test_headers, 'markdown', include_links=False)
    
    print(f"测试用例 1 - Markdown 格式（无链接）:")
    print(f"  格式: {result1['format']}")
    print(f"  条目数: {result1['total_items']}")
    print(f"  包含级别: {result1['levels_included']}")
    print(f"  内容:\n{result1['content']}")
    
    assert result1['format'] == 'markdown', "格式应该是 markdown"
    assert result1['total_items'] == 7, f"条目数应该是 7，实际 {result1['total_items']}"
    assert result1['levels_included'] == [1, 2, 3], f"级别应该是 [1, 2, 3]，实际 {result1['levels_included']}"
    
    # 测试用例 2: Markdown 格式（带链接）
    result2 = extractor.generate_toc(test_headers, 'markdown', include_links=True)
    
    print(f"\n测试用例 2 - Markdown 格式（带链接）:")
    print(f"  内容:\n{result2['content']}")
    
    assert '](#' in result2['content'], "应该包含锚点链接"
    
    # 测试用例 3: HTML 格式
    result3 = extractor.generate_toc(test_headers, 'html')
    
    print(f"\n测试用例 3 - HTML 格式:")
    print(f"  内容:\n{result3['content']}")
    
    assert result3['format'] == 'html', "格式应该是 html"
    assert '<ul>' in result3['content'] and '</ul>' in result3['content'], "应该包含 HTML 列表标签"
    
    # 测试用例 4: 文本格式
    result4 = extractor.generate_toc(test_headers, 'text')
    
    print(f"\n测试用例 4 - 文本格式:")
    print(f"  内容:\n{result4['content']}")
    
    assert result4['format'] == 'text', "格式应该是 text"
    assert '第' in result4['content'] and '行' in result4['content'], "应该包含行号信息"
    
    # 测试用例 5: 限制最大级别
    result5 = extractor.generate_toc(test_headers, 'markdown', max_level=2)
    
    print(f"\n测试用例 5 - 限制最大级别 (max_level=2):")
    print(f"  条目数: {result5['total_items']}")
    print(f"  包含级别: {result5['levels_included']}")
    print(f"  内容:\n{result5['content']}")
    
    assert result5['total_items'] == 6, f"限制级别后条目数应该是 6，实际 {result5['total_items']}"
    assert result5['levels_included'] == [1, 2], f"级别应该是 [1, 2]，实际 {result5['levels_included']}"
    
    print("  ✓ TOC 生成功能测试通过")


def test_chinese_numbering():
    """测试汉字编号识别功能"""
    print("\n=== 测试 4: 汉字编号识别功能 ===")
    
    extractor = MarkdownTOCExtractor()
    
    # 测试汉字数字转换
    test_cases = [
        ('一', 1), ('二', 2), ('三', 3), ('四', 4), ('五', 5),
        ('六', 6), ('七', 7), ('八', 8), ('九', 9), ('十', 10),
        ('十一', 11), ('十二', 12), ('十五', 15), ('十九', 19),
        ('二十', 20), ('三十', 30), ('五十', 50), ('九十', 90),
        ('二十一', 21), ('三十五', 35), ('五十八', 58), ('九十九', 99),
        ('壹', 1), ('贰', 2), ('叁', 3), ('肆', 4), ('伍', 5),
        ('陆', 6), ('柒', 7), ('捌', 8), ('玖', 9), ('拾', 10),
        ('百', None), ('千', None), ('万', None), ('abc', None)
    ]
    
    success_count = 0
    for chinese_num, expected in test_cases:
        result = extractor._chinese_number_to_int(chinese_num)
        if result == expected:
            success_count += 1
        else:
            print(f"❌ '{chinese_num}' -> {result} (期望: {expected})")
    
    assert success_count == len(test_cases), f"汉字数字转换测试失败，成功率: {success_count}/{len(test_cases)}"
    
    # 测试汉字编号标题提取
    chinese_content = """# 第一章 概述
## 第一节 背景
### 第一小节 历史
## 第二节 现状
# 第二章 方法
## 第一节 理论基础
### 第一小节 基本概念
### 第二小节 核心原理
## 第二节 实践应用
"""
    
    headers = extractor.extract_toc(chinese_content)
    assert len(headers) == 9, f"期望提取 9 个标题，实际 {len(headers)} 个"
    
    # 验证汉字编号识别
    numbered_headers = [h for h in headers if extractor._extract_number_from_title(h['title'], h['level']) is not None]
    assert len(numbered_headers) >= 6, f"期望至少识别 6 个汉字编号，实际 {len(numbered_headers)} 个"
    
    print("  ✓ 汉字编号识别测试通过")


def test_has_issues_meaning():
    """测试 has_issues 返回值的含义"""
    print("\n=== 测试 5: has_issues 含义验证 ===")
    
    extractor = MarkdownTOCExtractor()
    
    # 测试用例 1：正常编号文档
    normal_content = """# 文档标题
## 1. 第一章
### 1.1 小节1
### 1.2 小节2
## 2. 第二章
### 2.1 小节1
"""
    
    headers1 = extractor.extract_toc(normal_content)
    analysis1 = extractor.analyze_numbering_issues(headers1)
    assert not analysis1['has_issues'], "正常编号文档不应该有问题"
    assert len(analysis1['duplicate_numbers']) == 0, "正常编号文档不应该有重复编号"
    assert len(analysis1['discontinuous_numbers']) == 0, "正常编号文档不应该有不连续编号"
    
    # 测试用例 2：重复编号文档
    duplicate_content = """# 文档标题
## 1. 第一章
### 1.1 小节1
## 2. 第二章
### 1.1 小节1（重复编号）
"""
    
    headers2 = extractor.extract_toc(duplicate_content)
    analysis2 = extractor.analyze_numbering_issues(headers2)
    assert analysis2['has_issues'], "重复编号文档应该有问题"
    assert len(analysis2['duplicate_numbers']) > 0, "重复编号文档应该检测到重复编号"
    
    # 测试用例 3：不连续编号文档
    discontinuous_content = """# 文档标题
## 1. 第一章
## 3. 第三章（跳过了第二章）
## 4. 第四章
"""
    
    headers3 = extractor.extract_toc(discontinuous_content)
    analysis3 = extractor.analyze_numbering_issues(headers3)
    assert analysis3['has_issues'], "不连续编号文档应该有问题"
    assert len(analysis3['discontinuous_numbers']) > 0, "不连续编号文档应该检测到不连续编号"
    
    print("  ✓ has_issues 含义验证测试通过")


def test_convenience_functions():
    """测试便捷函数"""
    print("\n=== 测试 6: 便捷函数 ===")
    
    test_content = """# 1. 测试标题
## 1.1 子标题
# 1. 重复标题
"""
    
    # 测试便捷函数
    headers = extract_toc_from_content(test_content)
    issues = analyze_numbering_issues_from_headers(headers)
    toc = generate_toc_from_headers(headers, 'markdown', include_links=True)
    
    print(f"便捷函数测试:")
    print(f"  提取标题数: {len(headers)}")
    print(f"  存在编号问题: {issues['has_issues']}")
    print(f"  生成的 TOC 条目数: {toc['total_items']}")
    
    assert len(headers) == 3, f"应该提取到 3 个标题，实际 {len(headers)}"
    assert issues['has_issues'], "应该检测到编号问题"
    assert toc['total_items'] == 3, f"TOC 应该有 3 个条目，实际 {toc['total_items']}"
    
    print("  ✓ 便捷函数测试通过")


def main():
    """运行所有测试"""
    print("开始测试 Markdown TOC 核心功能...")
    
    try:
        test_toc_extraction()
        test_numbering_analysis()
        test_toc_generation()
        test_chinese_numbering()
        test_has_issues_meaning()
        test_convenience_functions()
        
        print("\n" + "="*50)
        print("🎉 所有测试通过！核心功能工作正常。")
        print("="*50)
        
        # 生成测试报告
        report = {
            "test_status": "PASSED",
            "total_tests": 6,
            "passed_tests": 6,
            "failed_tests": 0,
            "core_functions": {
                "toc_extraction": "✓ 正常",
                "numbering_analysis": "✓ 正常", 
                "toc_generation": "✓ 正常",
                "chinese_numbering": "✓ 正常",
                "has_issues_meaning": "✓ 正常",
                "convenience_functions": "✓ 正常"
            },
            "features_verified": [
                "基本标题提取",
                "特殊字符标题清理",
                "代码块过滤",
                "重复编号检测",
                "不连续编号检测",
                "Markdown TOC 生成",
                "HTML TOC 生成",
                "文本 TOC 生成",
                "锚点链接生成",
                "级别限制功能",
                "便捷函数接口"
            ]
        }
        
        ensure_directories()
        report_path = get_report_file_path('core_functions_test_report.json')
        
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