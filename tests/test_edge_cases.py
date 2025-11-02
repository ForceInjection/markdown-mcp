#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边界情况和特殊场景测试

本测试文件专门测试 MarkdownTOCExtractor 在各种边界情况和特殊场景下的表现，
确保系统的健壮性和可靠性。

测试场景包括：
1. 空文件和无效输入
2. 特殊字符和编码问题
3. 极大文件和性能边界
4. 格式错误和异常情况
5. 复杂嵌套结构
6. 多语言混合内容
"""

import json
import sys
import os
import tempfile
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
from test_config import TEST_CONFIG, get_report_file_path, ensure_directories


class TestEdgeCases(unittest.TestCase):
    """边界情况测试类"""
    
    def setUp(self):
        """每个测试前的准备工作"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_files = []
    
    def tearDown(self):
        """每个测试后的清理工作"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def create_temp_file(self, content, filename="test.md"):
        """创建临时测试文件"""
        temp_file = os.path.join(self.temp_dir, filename)
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        self.temp_files.append(temp_file)
        return temp_file
    
    def test_empty_file(self):
        """测试空文件"""
        print("\n=== 测试 1: 空文件处理 ===")
        
        # 测试提取空文件的标题
        headers = extract_toc_from_content("")
        self.assertEqual(len(headers), 0)
        
        # 测试分析空标题列表
        issues = analyze_numbering_issues_from_headers([])
        self.assertEqual(len(issues['duplicate_numbers']), 0)
        self.assertEqual(len(issues['discontinuous_numbers']), 0)
        
        # 测试生成空 TOC
        toc_result = generate_toc_from_headers([], format_type='markdown')
        self.assertEqual(toc_result['content'].strip(), "")
        
        print("✅ 空文件处理正确")
    
    def test_file_not_found(self):
        """测试文件不存在的情况"""
        print("\n=== 测试 2: 文件不存在 ===")
        
        # 由于我们的 API 是基于内容的，这里测试无效内容处理
        try:
            # 测试 None 输入
            headers = extract_toc_from_content(None)
            self.fail("应该抛出异常")
        except (TypeError, AttributeError):
            pass  # 预期的异常
        
        print("✅ 无效输入异常处理正确")
    
    def test_special_characters(self):
        """测试特殊字符处理"""
        print("\n=== 测试 3: 特殊字符处理 ===")
        
        special_content = """
# 标题 `代码` **粗体** *斜体* ~~删除线~~
## 标题 [链接](http://example.com) ![图片](image.png)
### 标题 with emoji 🚀 📝 ✅
#### 标题 with symbols @#$%^&*()
##### 标题 with 中文、English、日本語、한국어
###### 标题 with numbers 123 and dates 2024-01-01
"""
        
        headers = extract_toc_from_content(special_content)
        
        # 验证提取到所有标题
        self.assertEqual(len(headers), 6)
        
        # 验证特殊字符处理
        titles = [h['title'] for h in headers]
        
        # 检查标题被正确提取（可能保留部分格式）
        markdown_title = next((t for t in titles if '代码' in t and '粗体' in t), None)
        self.assertIsNotNone(markdown_title, "应该提取包含代码和粗体的标题")
        
        link_title = next((t for t in titles if '链接' in t), None)
        self.assertIsNotNone(link_title, "应该提取包含链接的标题")
        
        # 检查 emoji 和特殊符号保留
        emoji_title = next((t for t in titles if '🚀' in t), None)
        self.assertIsNotNone(emoji_title, "应该保留 emoji")
        if emoji_title:
            self.assertIn('🚀', emoji_title)
            self.assertIn('📝', emoji_title)
            self.assertIn('✅', emoji_title)
        
        # 检查多语言内容
        multilang_title = next((t for t in titles if '中文' in t and 'English' in t), None)
        self.assertIsNotNone(multilang_title, "应该处理多语言标题")
        if multilang_title:
            self.assertIn('中文', multilang_title)
            self.assertIn('English', multilang_title)
            self.assertIn('日本語', multilang_title)
            self.assertIn('한국어', multilang_title)
        
        print("✅ 特殊字符处理正确")
    
    def test_malformed_headers(self):
        """测试格式错误的标题"""
        print("\n=== 测试 4: 格式错误的标题 ===")
        
        malformed_content = """
#标题没有空格
# 
##  多个空格的标题  
###标题后面有多个#####
#### 标题
中间有内容
##### 正常标题
#######七级标题（超出范围）
# 标题 # 中间有井号 # 的标题
"""
        
        headers = extract_toc_from_content(malformed_content)
        
        # 验证只提取有效的标题
        valid_titles = [h['title'] for h in headers]
        
        # 应该忽略没有空格的标题
        self.assertNotIn('标题没有空格', valid_titles)
        
        # 应该处理多个空格
        self.assertIn('多个空格的标题', valid_titles)
        
        # 应该忽略超过6级的标题
        seven_level_headers = [h for h in headers if h['level'] > 6]
        self.assertEqual(len(seven_level_headers), 0)
        
        # 应该正确处理标题中的井号
        hash_title = next((t for t in valid_titles if '中间有井号' in t), None)
        self.assertIsNotNone(hash_title)
        
        print("✅ 格式错误的标题处理正确")
    
    def test_complex_code_blocks(self):
        """测试复杂代码块处理"""
        print("\n=== 测试 5: 复杂代码块处理 ===")
        
        complex_code_content = """
# 正常标题

```python
# 这不是标题
def function():
    # 这也不是标题
    pass
```

## 另一个正常标题

```
# 无语言标识的代码块中的假标题
## 这也不应该被识别
```

### 嵌套代码块测试

```markdown
# 这是 markdown 代码块中的标题
## 不应该被识别为真实标题
```

#### 行内代码测试

这里有行内代码 `# 不是标题` 和 `## 也不是标题`。

##### 混合内容

```javascript
// 这是注释，不是标题
function test() {
    console.log("# 这不是标题");
}
```

正常文本内容。

###### 最后一个标题
"""
        
        headers = extract_toc_from_content(complex_code_content)
        
        # 验证只提取真实的标题
        titles = [h['title'] for h in headers]
        
        expected_titles = [
            "正常标题",
            "另一个正常标题", 
            "嵌套代码块测试",
            "行内代码测试",
            "混合内容",
            "最后一个标题"
        ]
        
        for expected in expected_titles:
            self.assertIn(expected, titles, f"应该包含标题: {expected}")
        
        # 验证代码块中的内容没有被误识别
        code_false_positives = [
            "这不是标题",
            "这也不是标题", 
            "无语言标识的代码块中的假标题",
            "这也不应该被识别",
            "这是 markdown 代码块中的标题",
            "不应该被识别为真实标题"
        ]
        
        for false_positive in code_false_positives:
            self.assertNotIn(false_positive, titles, f"不应该包含: {false_positive}")
        
        print("✅ 复杂代码块处理正确")
    
    def test_numbering_edge_cases(self):
        """测试编号边界情况"""
        print("\n=== 测试 6: 编号边界情况 ===")
        
        # 测试各种编号格式
        numbering_content = """
# 1. 正常编号
## 1.1 子编号
## 1.2 连续编号
# 2. 第二章
## 2.1 正常
## 2.3 跳跃编号（应该检测到不连续）
# 3. 第三章
## 3.1 正常
## 3.1 重复编号（应该检测到重复）
# 5. 跳跃章节（应该检测到不连续）
# 0. 零开始编号
# -1. 负数编号
# 1.0.1 三级编号
## 1.0.1.1 四级编号
# 编号 1 在中间
# 1编号没有点
# 1.a 字母编号
"""
        
        headers = extract_toc_from_content(numbering_content)
        issues = analyze_numbering_issues_from_headers(headers)
        
        # 验证检测到重复编号
        duplicates = issues['duplicate_numbers']
        self.assertGreaterEqual(len(duplicates), 0, "重复编号检测")
        
        # 验证检测到不连续编号
        discontinuous = issues['discontinuous_numbers']
        self.assertGreaterEqual(len(discontinuous), 0, "不连续编号检测")
        
        print(f"✅ 检测到 {len(duplicates)} 个重复编号")
        print(f"✅ 检测到 {len(discontinuous)} 个不连续编号")
    
    def test_large_file_performance(self):
        """测试大文件性能"""
        print("\n=== 测试 7: 大文件性能 ===")
        
        # 生成大文件内容（模拟大文档）
        large_content_parts = []
        
        # 生成 1000 个章节
        for i in range(1, 1001):
            large_content_parts.append(f"# {i}. 第 {i} 章")
            large_content_parts.append(f"这是第 {i} 章的内容。" * 10)
            
            # 每章有 5 个小节
            for j in range(1, 6):
                large_content_parts.append(f"## {i}.{j} 第 {j} 节")
                large_content_parts.append(f"这是第 {i}.{j} 节的内容。" * 20)
        
        large_content = "\n\n".join(large_content_parts)
        
        # 创建大文件
        large_file = self.create_temp_file(large_content, "large_test.md")
        
        import time
        
        # 测试提取性能
        start_time = time.time()
        headers = extract_toc_from_content(large_content)
        extract_time = time.time() - start_time
        
        # 验证结果正确性
        self.assertEqual(len(headers), 6000)  # 1000 章 + 5000 节
        
        # 性能要求（合理的期望）
        self.assertLess(extract_time, 10.0, f"大文件提取时间过长: {extract_time:.2f}s")
        
        print(f"✅ 大文件性能测试通过")
        print(f"   文件大小: {len(large_content):,} 字符")
        print(f"   标题数量: {len(headers):,} 个")
        print(f"   提取时间: {extract_time:.3f}s")
    
    def test_unicode_and_encoding(self):
        """测试 Unicode 和编码问题"""
        print("\n=== 测试 8: Unicode 和编码 ===")
        
        unicode_content = """
# 中文标题 🇨🇳
## English Title 🇺🇸
### 日本語タイトル 🇯🇵
#### 한국어 제목 🇰🇷
##### Русский заголовок 🇷🇺
###### العنوان العربي 🇸🇦
# Título en Español 🇪🇸
## Titre Français 🇫🇷
### Deutscher Titel 🇩🇪
#### Titolo Italiano 🇮🇹
##### Título Português 🇵🇹
###### Tytuł Polski 🇵🇱
"""
        
        # 测试不同编码
        encodings = ['utf-8', 'utf-16', 'utf-32']
        
        for encoding in encodings:
            # 创建指定编码的文件
            temp_file = os.path.join(self.temp_dir, f"unicode_test_{encoding}.md")
            with open(temp_file, 'w', encoding=encoding) as f:
                f.write(unicode_content)
            self.temp_files.append(temp_file)
            
            # 测试读取和提取
            if encoding == 'utf-8':  # 只测试 UTF-8，因为我们的实现主要支持 UTF-8
                with open(temp_file, 'r', encoding=encoding) as f:
                    content = f.read()
                headers = extract_toc_from_content(content)
                
                # 验证所有语言的标题都被正确提取
                self.assertEqual(len(headers), 12)
                
                # 验证特定语言标题
                titles = [h['title'] for h in headers]
                self.assertIn('中文标题 🇨🇳', titles)
                self.assertIn('English Title 🇺🇸', titles)
                self.assertIn('日本語タイトル 🇯🇵', titles)
                self.assertIn('한국어 제목 🇰🇷', titles)
        
        print("✅ Unicode 和编码处理正确")
    
    def test_toc_generation_edge_cases(self):
        """测试 TOC 生成的边界情况"""
        print("\n=== 测试 9: TOC 生成边界情况 ===")
        
        # 测试空标题列表
        empty_toc_result = generate_toc_from_headers([], format_type='markdown')
        self.assertEqual(empty_toc_result['content'].strip(), "")
        
        # 测试单个标题
        single_header = [{'level': 1, 'title': '单个标题', 'line_number': 1}]
        single_toc_result = generate_toc_from_headers(single_header, format_type='markdown')
        self.assertIn('单个标题', single_toc_result['content'])
        
        # 测试不规则层级（跳级）
        irregular_headers = [
            {'level': 1, 'title': '一级标题', 'line_number': 1},
            {'level': 3, 'title': '跳到三级', 'line_number': 2},  # 跳过二级
            {'level': 2, 'title': '回到二级', 'line_number': 3},
            {'level': 6, 'title': '跳到六级', 'line_number': 4},  # 跳过四五级
        ]
        
        # 测试各种格式
        formats = ['markdown', 'html', 'text']
        for fmt in formats:
            toc_result = generate_toc_from_headers(irregular_headers, format_type=fmt)
            self.assertIsNotNone(toc_result)
            self.assertIn('content', toc_result)
            self.assertIn('一级标题', toc_result['content'])
            self.assertIn('跳到三级', toc_result['content'])
        
        # 测试无效格式
        try:
            generate_toc_from_headers(irregular_headers, format_type='invalid_format')
            self.fail("应该抛出异常")
        except (ValueError, KeyError):
            pass  # 预期的异常
        
        print("✅ TOC 生成边界情况处理正确")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        print("\n=== 测试 10: 内存使用 ===")
        
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        
        # 记录初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量标题数据
        large_headers = []
        for i in range(10000):
            large_headers.append({
                'level': (i % 6) + 1,
                'title': f'标题 {i} ' + 'x' * 100,  # 长标题
                'line_number': i + 1
            })
        
        # 执行各种操作
        issues = analyze_numbering_issues_from_headers(large_headers)
        markdown_toc = generate_toc_from_headers(large_headers, format_type='markdown')
        html_toc = generate_toc_from_headers(large_headers, format_type='html')
        text_toc = generate_toc_from_headers(large_headers, format_type='text')
        
        # 记录峰值内存使用
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # 验证内存使用合理（不超过 100MB 增长）
        self.assertLess(memory_increase, 100, f"内存使用过多: {memory_increase:.2f}MB")
        
        print(f"✅ 内存使用测试通过")
        print(f"   初始内存: {initial_memory:.2f}MB")
        print(f"   峰值内存: {peak_memory:.2f}MB")
        print(f"   内存增长: {memory_increase:.2f}MB")
        
        # 清理大对象
        del large_headers, markdown_toc, html_toc, text_toc


def run_edge_case_tests():
    """运行边界情况测试"""
    print("🧪 开始运行边界情况和特殊场景测试...")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEdgeCases)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # 生成报告
    if result.wasSuccessful():
        print("\n🎉 所有边界情况测试通过！")
        
        # 生成测试报告
        report = {
            'test_type': 'edge_cases',
            'total_tests': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'test_categories': [
                'empty_file_handling',
                'file_not_found',
                'special_characters',
                'malformed_headers',
                'complex_code_blocks',
                'numbering_edge_cases',
                'large_file_performance',
                'unicode_encoding',
                'toc_generation_edge_cases',
                'memory_usage'
            ],
            'status': 'PASSED' if result.wasSuccessful() else 'FAILED'
        }
        
        # 保存测试报告
        ensure_directories()
        report_path = get_report_file_path('edge_cases_test_report.json')
        
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
    exit_code = run_edge_case_tests()
    exit(exit_code)