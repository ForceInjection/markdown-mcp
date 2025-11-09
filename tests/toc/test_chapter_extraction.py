#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
章节提取功能测试

测试章节提取功能，特别是处理包含代码块的文档时的章节识别能力
"""

import os
import sys
import unittest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from markdown_toc.extractor import MarkdownTOCExtractor


class TestChapterExtraction(unittest.TestCase):
    """章节提取功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.extractor = MarkdownTOCExtractor()
        
        # Apache Spark 文档路径
        self.spark_doc_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'Apache Spark 设计与实现.md'
        )
        
        # 确保文档存在
        self.assertTrue(os.path.exists(self.spark_doc_path), 
                       "Apache Spark 文档不存在")
        
        # 读取文档内容
        with open(self.spark_doc_path, 'r', encoding='utf-8') as f:
            self.spark_content = f.read()
    
    def test_extract_all_chapters(self):
        """测试提取所有章节标题"""
        # 提取所有标题
        headers = self.extractor.extract_toc(self.spark_content)
        
        # 过滤出章节标题（以"第X章"开头）
        import re
        chapter_headers = [
            h for h in headers 
            if re.match(r'第\s*[一二三四五六七八九十\d]+\s*章', h['title'])
        ]
        
        # 验证找到4个章节
        self.assertEqual(len(chapter_headers), 4, 
                        f"应该找到4个章节，但实际找到 {len(chapter_headers)} 个")
        
        # 验证章节内容
        expected_chapters = [
            "第 1 章 Spark 概览与核心概念",
            "第 2 章 Spark 集群架构与执行机制", 
            "第 3 章 RDD：弹性分布式数据集",
            "第 4 章 Spark 作业执行机制"
        ]
        
        actual_chapters = [h['title'] for h in chapter_headers]
        
        for expected in expected_chapters:
            self.assertIn(expected, actual_chapters, 
                         f"章节 '{expected}' 未找到")
    
    def test_chapter_line_numbers(self):
        """测试章节行号正确性"""
        # 提取所有标题
        headers = self.extractor.extract_toc(self.spark_content)
        
        # 过滤出章节标题
        import re
        chapter_headers = [
            h for h in headers 
            if re.match(r'第\s*[一二三四五六七八九十\d]+\s*章', h['title'])
        ]
        
        # 验证章节行号（这些应该是大致的位置）
        # 注意：行号可能因文档编辑而略有变化
        chapter_line_numbers = [h['line_number'] for h in chapter_headers]
        
        # 行号应该是有序的
        self.assertEqual(chapter_line_numbers, sorted(chapter_line_numbers),
                        "章节行号应该是有序的")
        
        # 行号应该在合理范围内
        for line_num in chapter_line_numbers:
            self.assertGreater(line_num, 0, "行号应该大于0")
            self.assertLess(line_num, 5000, "行号应该在合理范围内")
    
    def test_chapter_levels(self):
        """测试章节级别正确性"""
        # 提取所有标题
        headers = self.extractor.extract_toc(self.spark_content)
        
        # 过滤出章节标题
        import re
        chapter_headers = [
            h for h in headers 
            if re.match(r'第\s*[一二三四五六七八九十\d]+\s*章', h['title'])
        ]
        
        # 所有章节应该是二级标题
        for chapter in chapter_headers:
            self.assertEqual(chapter['level'], 2, 
                           f"章节 '{chapter['title']}' 应该是二级标题")
    
    def test_no_false_positives(self):
        """测试不会误识别章节小结为章节"""
        # 提取所有标题
        headers = self.extractor.extract_toc(self.spark_content)
        
        # 过滤出章节标题（以"第X章"开头）
        import re
        chapter_headers = [
            h for h in headers 
            if re.match(r'第\s*[一二三四五六七八九十\d]+\s*章', h['title'])
        ]
        
        # 检查章节标题中不应该包含"小结"
        false_chapters = [
            h['title'] for h in chapter_headers
            if re.search(r'小结', h['title'])
        ]
        
        # 应该没有误识别的章节小结
        self.assertEqual(len(false_chapters), 0,
                        f"发现误识别的章节小结: {false_chapters}")


def test_chapter_extraction_with_code_blocks():
    """
    测试包含代码块的文档章节提取
    
    这个测试专门验证修复的问题：代码块内的章节标题应该被正确识别
    """
    extractor = MarkdownTOCExtractor()
    
    # 创建一个包含代码块的测试文档
    test_content = """
# 第 1 章 介绍

这是第一章的内容

```
## 第 2 章 代码中的章节（不应该被误识别）
这是代码块中的内容，不应该被提取为章节
```

## 第 2 章 实际章节

这是真正的第二章

```java
// 另一个代码块
## 第 3 章 另一个代码中的章节
不应该被识别
```

## 第 3 章 真正的第三章

内容
"""
    
    # 提取标题
    headers = extractor.extract_toc(test_content)
    
    # 过滤出章节标题
    import re
    chapter_headers = [
        h for h in headers 
        if re.match(r'第\s*[一二三四五六七八九十\d]+\s*章', h['title'])
    ]
    
    # 应该只找到3个真正的章节，而不是代码块中的假章节
    assert len(chapter_headers) == 3, f"应该找到3个章节，但找到 {len(chapter_headers)} 个"
    
    # 验证章节标题
    expected_titles = ["第 1 章 介绍", "第 2 章 实际章节", "第 3 章 真正的第三章"]
    actual_titles = [h['title'] for h in chapter_headers]
    
    for expected in expected_titles:
        assert expected in actual_titles, f"章节 '{expected}' 未找到"
    
    print("✅ 代码块章节提取测试通过")


if __name__ == '__main__':
    # 运行单元测试
    unittest.main(verbosity=2)
    
    # 运行额外的功能测试
    print("\n运行额外功能测试...")
    test_chapter_extraction_with_code_blocks()
    print("所有测试通过! 🎉")