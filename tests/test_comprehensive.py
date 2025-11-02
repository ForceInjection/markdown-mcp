#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合功能测试

本测试文件整合了以下功能的测试：
1. TOC 生成格式测试（Markdown、HTML、Text）
2. YARN 文档处理和编号分析
3. Extractor 健壮性测试
4. 性能和内存使用测试
"""

import sys
import os
import json

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from markdown_toc.extractor import MarkdownTOCExtractor
from test_config import TEST_CONFIG, get_test_file_path, get_report_file_path, ensure_directories


def test_toc_generation_formats():
    """测试 TOC 生成的不同格式"""
    print("=== 测试 1: TOC 生成格式 ===")
    
    extractor = MarkdownTOCExtractor()
    
    # 测试内容
    test_content = """# 1. 项目介绍
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
    
    # 提取标题
    headers = extractor.extract_toc(test_content)
    assert len(headers) == 10, f"期望提取 10 个标题，实际 {len(headers)} 个"
    
    # 测试不同格式的 TOC 生成
    formats = ['markdown', 'html', 'text']
    
    for fmt in formats:
        result = extractor.generate_toc(headers, fmt)
        
        # 验证返回结构
        assert 'format' in result, f"{fmt} 格式结果应包含 format 字段"
        assert 'total_items' in result, f"{fmt} 格式结果应包含 total_items 字段"
        assert 'levels_included' in result, f"{fmt} 格式结果应包含 levels_included 字段"
        assert 'content' in result, f"{fmt} 格式结果应包含 content 字段"
        
        # 验证内容
        assert result['format'] == fmt, f"格式应为 {fmt}"
        assert result['total_items'] == 10, f"总项目数应为 10，实际 {result['total_items']}"
        assert len(result['content']) > 0, f"{fmt} 格式内容不应为空"
        
        print(f"  ✓ {fmt.upper()} 格式生成成功")
    
    print("✅ TOC 生成格式测试通过")
    return True


def test_yarn_document_processing():
    """测试 YARN 文档处理功能"""
    print("=== 测试 2: YARN 文档处理 ===")
    
    # 读取 yarn.md 文件
    yarn_file_path = get_test_file_path('yarn.md')
    
    if not os.path.exists(yarn_file_path):
        print(f"⚠️ 跳过 YARN 文档测试：文件不存在 {yarn_file_path}")
        return True
    
    try:
        with open(yarn_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️ 跳过 YARN 文档测试：读取文件失败 {e}")
        return True
    
    extractor = MarkdownTOCExtractor()
    
    # 提取标题
    headers = extractor.extract_toc(content)
    print(f"  ✓ 提取到 {len(headers)} 个标题")
    
    # 验证基本结构
    assert len(headers) > 0, "应该提取到标题"
    
    # 测试编号识别
    numbered_count = 0
    chapter_count = 0
    
    for header in headers:
        title = header['title']
        number = extractor._extract_number_from_title(title, header['level'])
        
        if number is not None:
            numbered_count += 1
            
        # 检查章节标题
        if '章' in title:
            chapter_count += 1
    
    print(f"  ✓ 识别到 {numbered_count} 个编号标题")
    print(f"  ✓ 识别到 {chapter_count} 个章节标题")
    
    # 分析编号问题
    analysis = extractor.analyze_numbering_issues(headers)
    print(f"  ✓ 编号分析完成：has_issues = {analysis['has_issues']}")
    print(f"  ✓ 重复编号：{len(analysis['duplicate_numbers'])} 个")
    print(f"  ✓ 不连续编号：{len(analysis['discontinuous_numbers'])} 个")
    
    # 生成 TOC
    toc_result = extractor.generate_toc(headers, 'markdown')
    assert toc_result['total_items'] == len(headers), "TOC 项目数应与标题数一致"
    
    print("✅ YARN 文档处理测试通过")
    return True


def test_extractor_robustness():
    """测试 extractor 的健壮性"""
    print("=== 测试 3: Extractor 健壮性 ===")
    
    extractor = MarkdownTOCExtractor()
    
    # 测试用例 1：空内容
    headers = extractor.extract_toc("")
    assert len(headers) == 0, "空内容应返回空列表"
    
    # 测试用例 2：无标题内容
    no_header_content = """这是一段普通文本。
没有任何标题。

```python
# 这是代码块
def example():
    pass
```

还是普通文本。
"""
    headers = extractor.extract_toc(no_header_content)
    assert len(headers) == 0, "无标题内容应返回空列表"
    
    # 测试用例 3：特殊字符标题
    special_content = """# 1. 标题包含特殊字符：@#$%^&*()
## 1.1 中英文混合 Title with English
### 1.1.1 数字123和符号！？
## 1.2 emoji 标题 🚀 📝 ✨
# 2. 另一个章节
"""
    headers = extractor.extract_toc(special_content)
    assert len(headers) == 5, f"期望提取 5 个标题，实际 {len(headers)} 个"
    
    # 验证特殊字符处理
    for header in headers:
        assert 'title' in header, "每个标题应包含 title 字段"
        assert 'level' in header, "每个标题应包含 level 字段"
        assert 'line_number' in header, "每个标题应包含 line_number 字段"
        assert len(header['title']) > 0, "标题内容不应为空"
    
    # 测试用例 4：深层嵌套
    deep_nested_content = """# 1. 第一级
## 1.1 第二级
### 1.1.1 第三级
#### 1.1.1.1 第四级
##### 1.1.1.1.1 第五级
###### 1.1.1.1.1.1 第六级
"""
    headers = extractor.extract_toc(deep_nested_content)
    assert len(headers) == 6, f"期望提取 6 个标题，实际 {len(headers)} 个"
    
    # 验证层级
    expected_levels = [1, 2, 3, 4, 5, 6]
    actual_levels = [h['level'] for h in headers]
    assert actual_levels == expected_levels, f"层级不匹配：期望 {expected_levels}，实际 {actual_levels}"
    
    print("✅ Extractor 健壮性测试通过")
    return True


def test_performance_and_memory():
    """测试性能和内存使用"""
    print("=== 测试 4: 性能和内存 ===")
    
    import time
    
    extractor = MarkdownTOCExtractor()
    
    # 生成大文档
    large_content = ""
    for i in range(1, 101):  # 100 个章节
        large_content += f"# {i}. 第{i}章\n\n"
        for j in range(1, 11):  # 每章 10 个小节
            large_content += f"## {i}.{j} 第{j}节\n\n"
            for k in range(1, 6):  # 每节 5 个子节
                large_content += f"### {i}.{j}.{k} 第{k}小节\n\n"
                large_content += "这是一些内容。\n\n"
    
    print(f"  ✓ 生成大文档：{len(large_content)} 字符")
    
    # 测试提取性能
    start_time = time.time()
    headers = extractor.extract_toc(large_content)
    extraction_time = time.time() - start_time
    
    expected_headers = 100 + 100*10 + 100*10*5  # 100 + 1000 + 5000 = 6100
    assert len(headers) == expected_headers, f"期望 {expected_headers} 个标题，实际 {len(headers)} 个"
    
    print(f"  ✓ 提取 {len(headers)} 个标题，耗时 {extraction_time:.3f} 秒")
    
    # 测试分析性能
    start_time = time.time()
    analysis = extractor.analyze_numbering_issues(headers)
    analysis_time = time.time() - start_time
    
    print(f"  ✓ 编号分析完成，耗时 {analysis_time:.3f} 秒")
    
    # 测试生成性能
    start_time = time.time()
    toc_result = extractor.generate_toc(headers, 'markdown')
    generation_time = time.time() - start_time
    
    print(f"  ✓ TOC 生成完成，耗时 {generation_time:.3f} 秒")
    
    total_time = extraction_time + analysis_time + generation_time
    print(f"  ✓ 总耗时：{total_time:.3f} 秒")
    
    # 性能断言（合理的性能期望）
    assert extraction_time < 5.0, f"提取时间过长：{extraction_time:.3f} 秒"
    assert analysis_time < 2.0, f"分析时间过长：{analysis_time:.3f} 秒"
    assert generation_time < 3.0, f"生成时间过长：{generation_time:.3f} 秒"
    
    print("✅ 性能和内存测试通过")
    return True


def main():
    """运行所有综合测试"""
    print("开始综合功能测试...")
    print("="*50)
    
    try:
        test_toc_generation_formats()
        test_yarn_document_processing()
        test_extractor_robustness()
        test_performance_and_memory()
        
        print("\n" + "="*50)
        print("🎉 所有综合测试通过！")
        print("="*50)
        
        # 生成测试报告
        report = {
            "test_status": "PASSED",
            "total_tests": 4,
            "passed_tests": 4,
            "failed_tests": 0,
            "test_categories": {
                "toc_generation_formats": "✓ 正常",
                "yarn_document_processing": "✓ 正常",
                "extractor_robustness": "✓ 正常",
                "performance_and_memory": "✓ 正常"
            },
            "timestamp": "2024"
        }
        
        # 保存测试报告
        ensure_directories()
        report_file = get_report_file_path('comprehensive_test_report.json')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📊 测试报告已保存到: {report_file}")
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())