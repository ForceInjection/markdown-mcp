#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 yarn.md 的集成测试

本测试文件使用真实的 yarn.md 文档作为测试数据，验证 MarkdownTOCExtractor 
在处理复杂文档时的各项功能，包括：

1. 复杂标题结构的提取
2. 中英文混合内容的处理
3. 代码块和特殊字符的处理
4. 大文档的性能测试
5. 编号问题的检测
6. TOC 生成的准确性
"""

import json
import sys
import os
import time
import unittest
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from markdown_toc.extractor import (
    MarkdownTOCExtractor, 
    extract_toc_from_content, 
    analyze_numbering_issues_from_headers, 
    generate_toc_from_headers
)
from test_config import TEST_CONFIG, get_test_file_path, get_report_file_path, ensure_directories


class TestYarnIntegration(unittest.TestCase):
    """基于 yarn.md 的集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.yarn_file_path = get_test_file_path('yarn.md')
        
        # 验证测试文件存在
        if not os.path.exists(cls.yarn_file_path):
            raise FileNotFoundError(f"测试文件不存在: {cls.yarn_file_path}")
        
        # 读取文件内容
        with open(cls.yarn_file_path, 'r', encoding='utf-8') as f:
            cls.content = f.read()
        
        print(f"✅ 测试文件加载成功: {cls.yarn_file_path}")
        print(f"📄 文件大小: {len(cls.content)} 字符")
        print(f"📝 文件行数: {len(cls.content.splitlines())} 行")
    
    def test_file_reading(self):
        """测试文件读取功能"""
        print("\n=== 测试 1: 文件读取功能 ===")
        
        # 测试文件读取
        content = self.content
        
        # 验证内容不为空
        self.assertIsNotNone(content)
        self.assertGreater(len(content), 0)
        
        # 验证包含预期的标题
        self.assertIn("# YARN 分布式资源管理与调度", content)
        self.assertIn("## 第 1 章 YARN 设计原理与架构", content)
        
        print(f"✅ 文件读取成功，内容长度: {len(content)} 字符")
    
    def test_header_extraction(self):
        """测试标题提取功能"""
        print("\n=== 测试 2: 标题提取功能 ===")
        
        # 提取标题
        headers = extract_toc_from_content(self.content)
        
        # 验证提取到标题
        self.assertIsInstance(headers, list)
        self.assertGreater(len(headers), 0)
        
        # 验证标题结构
        found_main_title = False
        found_chapter_title = False
        found_section_title = False
        
        for header in headers:
            self.assertIn('level', header)
            self.assertIn('title', header)
            self.assertIn('line_number', header)
            
            # 检查特定标题
            if header['title'] == "YARN 分布式资源管理与调度：原理、架构与实现":
                found_main_title = True
                self.assertEqual(header['level'], 1)
            
            if "第 1 章 YARN 设计原理与架构" in header['title']:
                found_chapter_title = True
                self.assertEqual(header['level'], 2)
            
            if "大数据发展背景" in header['title']:
                found_section_title = True
                self.assertEqual(header['level'], 3)
        
        self.assertTrue(found_main_title, "未找到主标题")
        self.assertTrue(found_chapter_title, "未找到章节标题")
        self.assertTrue(found_section_title, "未找到小节标题")
        
        print(f"✅ 成功提取 {len(headers)} 个标题")
        
        # 打印前 10 个标题作为示例
        print("📋 前 10 个标题:")
        for i, header in enumerate(headers[:10]):
            indent = "  " * (header['level'] - 1)
            print(f"   {indent}{'#' * header['level']} {header['title']} (行 {header['line_number']})")
    
    def test_chinese_english_mixed_content(self):
        """测试中英文混合内容的处理"""
        print("\n=== 测试 3: 中英文混合内容处理 ===")
        
        headers = extract_toc_from_content(self.content)
        
        # 查找包含英文的标题
        mixed_content_headers = []
        for header in headers:
            title = header['title']
            # 检查是否包含中英文混合
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in title)
            has_english = any(char.isalpha() and ord(char) < 128 for char in title)
            
            if has_chinese and has_english:
                mixed_content_headers.append(header)
        
        self.assertGreater(len(mixed_content_headers), 0, "应该包含中英文混合的标题")
        
        print(f"✅ 找到 {len(mixed_content_headers)} 个中英文混合标题")
        
        # 打印示例
        for header in mixed_content_headers[:5]:
            print(f"   📝 {header['title']}")
    
    def test_code_block_handling(self):
        """测试代码块处理"""
        print("\n=== 测试 4: 代码块处理 ===")
        
        # 检查原始内容是否包含代码块
        self.assertIn("```", self.content, "测试文档应包含代码块")
        
        # 提取标题（应该正确处理代码块）
        headers = extract_toc_from_content(self.content)
        
        # 验证代码块中的内容没有被误识别为标题
        code_block_false_headers = []
        for header in headers:
            # 检查是否有明显的代码内容被误识别
            title = header['title'].strip()
            if (title.startswith('│') or 
                title.startswith('├') or 
                title.startswith('└') or 
                title.startswith('┌') or
                'Node' in title and 'TaskTracker' in title):
                code_block_false_headers.append(header)
        
        # 代码块内容不应被识别为标题
        self.assertEqual(len(code_block_false_headers), 0, 
                        f"发现 {len(code_block_false_headers)} 个代码块内容被误识别为标题")
        
        print("✅ 代码块处理正确，未发现误识别")
    
    def test_numbering_analysis(self):
        """测试编号问题分析"""
        print("\n=== 测试 5: 编号问题分析 ===")
        
        headers = extract_toc_from_content(self.content)
        issues = analyze_numbering_issues_from_headers(headers)
        
        self.assertIsInstance(issues, dict)
        self.assertIn('has_issues', issues)
        self.assertIn('duplicate_numbers', issues)
        self.assertIn('discontinuous_numbers', issues)
        self.assertIn('statistics', issues)
        
        # 验证统计信息
        stats = issues['statistics']
        self.assertIn('total_headers', stats)
        self.assertIn('numbered_headers', stats)
        self.assertIn('levels_with_issues', stats)
        
        print(f"✅ 编号分析完成")
        print(f"   总标题数: {stats['total_headers']}")
        print(f"   编号标题数: {stats['numbered_headers']}")
        print(f"   有问题的层级数: {stats['levels_with_issues']}")
        print(f"   是否有问题: {issues['has_issues']}")
        
        if issues['duplicate_numbers']:
            print(f"   重复编号: {len(issues['duplicate_numbers'])} 个")
        
        if issues['discontinuous_numbers']:
            print(f"   不连续编号: {len(issues['discontinuous_numbers'])} 个")
    
    def test_toc_generation(self):
        """测试 TOC 生成功能"""
        print("\n=== 测试 6: TOC 生成功能 ===")
        
        # 先提取标题
        headers = extract_toc_from_content(self.content)
        
        # 测试不同格式的 TOC 生成
        formats = ['markdown', 'html', 'text']
        
        for fmt in formats:
            toc_result = generate_toc_from_headers(headers, format_type=fmt)
            
            self.assertIsInstance(toc_result, dict)
            self.assertIn('content', toc_result)
            
            content = toc_result['content']
            self.assertIsNotNone(content)
            self.assertGreater(len(content), 0)
            
            if fmt == 'markdown':
                self.assertIn('- ', content)  # Markdown 列表标记
            elif fmt == 'html':
                self.assertIn('<ul>', content)
                self.assertIn('</ul>', content)
            elif fmt == 'text':
                lines = content.split('\n')
                self.assertGreater(len(lines), 1)
            
            print(f"✅ {fmt.upper()} 格式 TOC 生成成功")
    
    def test_performance(self):
        """测试性能"""
        print("\n=== 测试 7: 性能测试 ===")
        
        # 测试文件读取性能
        start_time = time.time()
        content = self.content
        read_time = time.time() - start_time
        
        # 测试标题提取性能
        start_time = time.time()
        headers = extract_toc_from_content(content)
        extract_time = time.time() - start_time
        
        # 测试编号分析性能
        start_time = time.time()
        issues = analyze_numbering_issues_from_headers(headers)
        analysis_time = time.time() - start_time
        
        # 测试 TOC 生成性能
        start_time = time.time()
        toc = generate_toc_from_headers(headers, format_type='markdown')
        generation_time = time.time() - start_time
        
        print(f"⏱️ 性能测试结果:")
        print(f"   文件读取: {read_time:.3f}s")
        print(f"   标题提取: {extract_time:.3f}s")
        print(f"   编号分析: {analysis_time:.3f}s")
        print(f"   TOC 生成: {generation_time:.3f}s")
        print(f"   总耗时: {read_time + extract_time + analysis_time + generation_time:.3f}s")
        
        # 性能断言（合理的性能期望）
        self.assertLess(read_time, 1.0, "文件读取时间应小于 1 秒")
        self.assertLess(extract_time, 2.0, "标题提取时间应小于 2 秒")
        self.assertLess(analysis_time, 1.0, "编号分析时间应小于 1 秒")
        self.assertLess(generation_time, 1.0, "TOC 生成时间应小于 1 秒")
        
        print("✅ 性能测试通过")
    
    def test_edge_cases(self):
        """测试边界情况"""
        print("\n=== 测试 8: 边界情况处理 ===")
        
        # 测试空内容
        empty_headers = extract_toc_from_content("")
        self.assertEqual(len(empty_headers), 0)
        
        # 测试只有代码块的内容
        code_only_content = """
```python
# 这是代码
def hello():
    print("Hello")
```
"""
        code_headers = extract_toc_from_content(code_only_content)
        self.assertEqual(len(code_headers), 0)
        
        # 测试特殊字符标题
        special_content = """
# 标题 `代码` **粗体** *斜体*
## 标题 [链接](http://example.com)
### 标题 with English and 中文
"""
        special_headers = extract_toc_from_content(special_content)
        self.assertEqual(len(special_headers), 3)
        
        # 验证特殊字符被正确处理
        titles = [h['title'] for h in special_headers]
        self.assertIn('标题 代码 粗体 斜体', titles)
        self.assertIn('标题 链接', titles)
        self.assertIn('标题 with English and 中文', titles)
        
        print("✅ 边界情况处理正确")
    
    def test_integration_workflow(self):
        """测试完整工作流程"""
        print("\n=== 测试 9: 完整工作流程 ===")
        
        # 完整的工作流程：读取 -> 提取 -> 分析 -> 生成
        
        # 1. 读取文件
        content = self.content
        self.assertIsNotNone(content)
        
        # 2. 提取标题
        headers = extract_toc_from_content(content)
        self.assertGreater(len(headers), 0)
        
        # 3. 分析编号问题
        issues = analyze_numbering_issues_from_headers(headers)
        self.assertIsInstance(issues, dict)
        
        # 4. 生成不同格式的 TOC
        markdown_toc = generate_toc_from_headers(headers, format_type='markdown')
        html_toc = generate_toc_from_headers(headers, format_type='html')
        text_toc = generate_toc_from_headers(headers, format_type='text')
        
        # 验证所有步骤都成功
        self.assertIsInstance(markdown_toc, dict)
        self.assertIsInstance(html_toc, dict)
        self.assertIsInstance(text_toc, dict)
        
        print("✅ 完整工作流程测试通过")
        
        # 生成测试报告
        report = {
            'test_file': self.yarn_file_path,
            'file_size': len(content),
            'line_count': len(content.splitlines()),
            'headers_extracted': len(headers),
            'numbering_issues': {
                'duplicates': len(issues['duplicate_numbers']),
                'discontinuous': len(issues['discontinuous_numbers'])
            },
            'toc_formats_generated': ['markdown', 'html', 'json'],
            'test_status': 'PASSED'
        }
        
        return report


def run_yarn_integration_tests():
    """运行 yarn.md 集成测试"""
    print("🚀 开始运行基于 yarn.md 的集成测试...")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestYarnIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # 生成详细报告
    if result.wasSuccessful():
        print("\n🎉 所有测试通过！")
        
        # 运行完整工作流程测试获取报告
        TestYarnIntegration.setUpClass()
        test_instance = TestYarnIntegration()
        report = test_instance.test_integration_workflow()
        
        # 保存测试报告
        ensure_directories()
        report_path = get_report_file_path('yarn_integration_test_report.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📊 测试报告已保存: {report_path}")
        
        return 0
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
        for test, traceback in result.failures + result.errors:
            print(f"   ❌ {test}: {traceback}")
        
        return 1


if __name__ == "__main__":
    exit_code = run_yarn_integration_tests()
    exit(exit_code)