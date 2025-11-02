#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOC 生成功能测试

本测试文件专门测试 generate_toc 功能的正确性，包括：
1. 基本 TOC 生成功能 - 验证基础的目录生成能力
2. 不同格式的 TOC 输出 - 测试 Markdown、HTML、Text 格式
3. 参数配置的正确性 - 验证各种配置参数的效果
4. 性能测试 - 测试大文档的 TOC 生成性能
5. README 文件测试 - 验证实际项目文档的处理能力
"""

import sys
import os
import time
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

# 导入测试配置和核心模块
from test_config import TEST_CONFIG, TEST_STATUS, get_report_file_path, ensure_directories, get_test_data
from markdown_toc.extractor import MarkdownTOCExtractor


class TestGenerateTOC:
    """TOC 生成功能测试类"""
    
    def __init__(self):
        self.extractor = MarkdownTOCExtractor()
        self.test_results = []
        self.readme_path = os.path.join(project_root, "README.md")
    
    def log_test_result(self, test_name, status, details=None, duration=0):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "duration": round(duration, 3),
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status_symbol = TEST_STATUS.get(status, status)
        print(f"{status_symbol} {test_name} ({duration:.3f}s)")
        
        if status == "FAILED" and details:
            print(f"   错误: {details.get('error', 'Unknown error')}")
    
    def test_basic_toc_generation(self):
        """测试基本 TOC 生成功能"""
        test_name = "基本 TOC 生成功能"
        start_time = time.time()
        
        try:
            # 使用测试数据
            content = get_test_data("standard_content")
            
            # 提取标题
            headers = self.extractor.extract_toc(content)
            
            # 生成 TOC
            toc_result = self.extractor.generate_toc(
                headers, 
                format_type='markdown', 
                include_links=True,
                max_level=3
            )
            
            # 验证结果
            assert 'content' in toc_result, "结果中缺少 content 字段"
            assert 'format' in toc_result, "结果中缺少 format 字段"
            assert 'total_items' in toc_result, "结果中缺少 total_items 字段"
            assert 'levels_included' in toc_result, "结果中缺少 levels_included 字段"
            assert toc_result['format'] == 'markdown', "格式不正确"
            assert toc_result['total_items'] > 0, "总条目数应大于 0"
            
            duration = time.time() - start_time
            self.log_test_result(test_name, "PASSED", {
                "headers_count": len(headers),
                "total_items": toc_result['total_items'],
                "format": toc_result['format'],
                "levels_included": toc_result['levels_included']
            }, duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, "FAILED", {"error": str(e)}, duration)
            return False
    
    def test_different_formats(self):
        """测试不同格式的 TOC 输出"""
        test_name = "不同格式 TOC 输出"
        start_time = time.time()
        
        try:
            content = get_test_data("standard_content")
            headers = self.extractor.extract_toc(content)
            
            formats = ['markdown', 'html', 'text']
            format_results = {}
            
            for fmt in formats:
                toc_result = self.extractor.generate_toc(
                    headers, 
                    format_type=fmt, 
                    include_links=False,
                    max_level=6
                )
                
                assert toc_result['format'] == fmt, f"格式 {fmt} 不正确"
                format_results[fmt] = {
                    "total_items": toc_result['total_items'],
                    "content_length": len(toc_result['content'])
                }
            
            duration = time.time() - start_time
            self.log_test_result(test_name, "PASSED", {
                "formats_tested": formats,
                "results": format_results
            }, duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, "FAILED", {"error": str(e)}, duration)
            return False
    
    def test_readme_file(self):
        """测试 README.md 文件的 TOC 生成"""
        test_name = "README.md TOC 生成"
        start_time = time.time()
        
        try:
            if not os.path.exists(self.readme_path):
                self.log_test_result(test_name, "SKIPPED", {"reason": "README.md 文件不存在"}, 0)
                return True
            
            with open(self.readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            headers = self.extractor.extract_toc(content)
            
            # 生成 TOC
            toc_result = self.extractor.generate_toc(
                headers, 
                format_type='markdown', 
                include_links=True,
                max_level=3
            )
            
            # 验证结果
            assert len(headers) > 0, "README.md 中应该有标题"
            assert toc_result['total_items'] > 0, "生成的 TOC 应该有内容"
            
            duration = time.time() - start_time
            self.log_test_result(test_name, "PASSED", {
                "file_path": self.readme_path,
                "headers_count": len(headers),
                "total_items": toc_result['total_items'],
                "content_preview": toc_result['content'][:200] + "..." if len(toc_result['content']) > 200 else toc_result['content']
            }, duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, "FAILED", {"error": str(e)}, duration)
            return False
    
    def test_performance(self):
        """测试性能"""
        test_name = "TOC 生成性能测试"
        start_time = time.time()
        
        try:
            # 创建大量标题的测试内容
            large_content = ""
            for i in range(1, 101):  # 100 个一级标题
                large_content += f"# {i}. 标题 {i}\n"
                for j in range(1, 6):  # 每个一级标题下 5 个二级标题
                    large_content += f"## {i}.{j} 子标题 {i}.{j}\n"
            
            # 提取标题
            headers = self.extractor.extract_toc(large_content)
            
            # 测试生成时间
            gen_start = time.time()
            toc_result = self.extractor.generate_toc(
                headers, 
                format_type='markdown', 
                include_links=True,
                max_level=6
            )
            gen_duration = time.time() - gen_start
            
            # 检查性能限制
            max_generation_time = TEST_CONFIG["performance"]["max_generation_time"]
            performance_ok = gen_duration <= max_generation_time
            
            duration = time.time() - start_time
            self.log_test_result(test_name, "PASSED" if performance_ok else "FAILED", {
                "headers_count": len(headers),
                "generation_time": round(gen_duration, 3),
                "max_allowed_time": max_generation_time,
                "performance_ok": performance_ok,
                "total_items": toc_result['total_items']
            }, duration)
            
            return performance_ok
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, "FAILED", {"error": str(e)}, duration)
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("TOC 生成功能测试")
        print("=" * 50)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        tests = [
            self.test_basic_toc_generation,
            self.test_different_formats,
            self.test_readme_file,
            self.test_performance
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test in tests:
            try:
                result = test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ 测试执行异常: {e}")
                failed += 1
        
        # 统计跳过的测试
        for result in self.test_results:
            if result["status"] == "SKIPPED":
                skipped += 1
                passed -= 1  # 调整计数
        
        # 输出总结
        total = len(tests)
        print("\n" + "=" * 50)
        print("测试总结")
        print("=" * 50)
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"跳过: {skipped}")
        print(f"成功率: {(passed/total*100):.1f}%")
        
        # 保存测试报告
        self.save_test_report()
        
        return failed == 0
    
    def save_test_report(self):
        """保存测试报告"""
        try:
            ensure_directories()
            report_file = get_report_file_path("generate_toc_test_report.json")
            
            report = {
                "test_type": "TOC 生成功能测试",
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed": len([r for r in self.test_results if r["status"] == "PASSED"]),
                "failed": len([r for r in self.test_results if r["status"] == "FAILED"]),
                "skipped": len([r for r in self.test_results if r["status"] == "SKIPPED"]),
                "test_results": self.test_results
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n📊 测试报告已保存到: {report_file}")
            
        except Exception as e:
            print(f"⚠️ 保存测试报告失败: {e}")


def main():
    """主函数"""
    tester = TestGenerateTOC()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 所有 TOC 生成功能测试通过！")
        return 0
    else:
        print("\n❌ 部分 TOC 生成功能测试失败！")
        return 1


if __name__ == "__main__":
    exit(main())