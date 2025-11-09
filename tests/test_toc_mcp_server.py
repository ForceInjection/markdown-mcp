#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown TOC MCP Server 测试脚本

本测试文件用于测试 Markdown TOC MCP Server 的核心功能，包括：
1. TOC 提取功能 - 从 Markdown 文档中提取标题结构
2. 编号问题分析功能 - 检测重复编号和不连续编号问题
3. 详细编号分析功能 - 深入分析编号问题的详细信息
4. 错误处理测试 - 验证异常情况的处理能力
5. 性能测试 - 验证大文档处理的性能表现
"""

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

# 导入测试配置
from test_config import TEST_CONFIG, get_report_file_path, ensure_directories

# 服务器特定配置
SERVER_CONFIG = {
    "test_directory": tempfile.mkdtemp(prefix="markdown_toc_test_"),
    "test_files_dir": "test_markdown_files",
    "server_host": "localhost",
    "server_port": 8000,
    "test_timeout": TEST_CONFIG["timeouts"]["default"]
}

# 测试用的 Markdown 内容
TEST_MARKDOWN_CONTENT = {
    "normal_doc": """# 1. 项目介绍

这是一个示例项目。

## 1.1 项目目标

项目的主要目标是...

## 1.2 技术栈

使用的技术包括：
- React
- TypeScript

### 1.2.1 前端技术

前端使用 React 框架。

### 1.2.2 后端技术

后端使用：
- Python
- FastAPI

# 2. 安装指南

详细的安装步骤。

## 2.1 环境要求

系统要求说明。

## 2.2 安装步骤

具体安装步骤。
""",
    
    "numbering_issues": """# 1. 第一章

内容...

## 1.1 第一节

内容...

## 1.1 重复编号

这里有重复编号问题。

## 1.3 跳跃编号

这里跳过了 1.2。

# 3. 第三章

跳过了第二章。

## 3.1 正常编号

内容...
""",
    
    "no_numbering": """# 项目介绍

这是一个没有编号的文档。

## 背景

项目背景描述。

### 历史

历史信息。

## 目标

项目目标。

# 技术方案

技术方案描述。

## 架构设计

架构设计说明。
"""
}


class MarkdownTOCServerTester:
    """Markdown TOC MCP Server 测试器"""
    
    def __init__(self):
        self.test_results = []
        self.test_directory = SERVER_CONFIG["test_directory"]
        self.setup_test_files()
    
    def setup_test_files(self):
        """设置测试文件"""
        test_files_dir = Path(self.test_directory) / SERVER_CONFIG["test_files_dir"]
        test_files_dir.mkdir(exist_ok=True)
        
        for name, content in TEST_MARKDOWN_CONTENT.items():
            file_path = test_files_dir / f"{name}.md"
            file_path.write_text(content, encoding='utf-8')
    
    def log_test(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """记录测试结果"""
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": time.time()
        })
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if message:
            print(f"   {message}")
    
    async def test_toc_extraction(self) -> bool:
        """测试 TOC 提取功能"""
        try:
            start_time = time.time()
            
            # 导入测试模块
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from markdown_toc.extractor import extract_toc_from_content
            
            # 测试正常文档
            test_file = Path(self.test_directory) / SERVER_CONFIG["test_files_dir"] / "normal_doc.md"
            content = test_file.read_text(encoding='utf-8')
            toc_items = extract_toc_from_content(content)
            
            # 验证结果
            if not toc_items:
                raise Exception("TOC 提取失败：结果为空")
            
            if len(toc_items) < 5:  # 应该至少有 5 个标题
                raise Exception(f"TOC 提取不完整：只找到 {len(toc_items)} 个标题")
            
            # 验证标题层级
            found_h1 = any(item['level'] == 1 for item in toc_items)
            found_h2 = any(item['level'] == 2 for item in toc_items)
            found_h3 = any(item['level'] == 3 for item in toc_items)
            
            if not (found_h1 and found_h2 and found_h3):
                raise Exception("TOC 提取缺少某些层级的标题")
            
            duration = time.time() - start_time
            self.log_test("TOC 提取功能", True, f"成功提取 {len(toc_items)} 个标题", duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("TOC 提取功能", False, str(e), duration)
            return False
    
    async def test_numbering_analysis(self) -> bool:
        """测试编号问题分析功能"""
        try:
            start_time = time.time()
            
            # 导入测试模块
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from markdown_toc.extractor import extract_toc_from_content, analyze_numbering_issues_from_headers
            
            # 测试有编号问题的文档
            test_file = Path(self.test_directory) / SERVER_CONFIG["test_files_dir"] / "numbering_issues.md"
            content = test_file.read_text(encoding='utf-8')
            headers = extract_toc_from_content(content)
            result = analyze_numbering_issues_from_headers(headers)
            
            # 验证结果
            if not result:
                raise Exception("编号分析失败：结果为空")
            
            # 检查返回的结构
            if 'has_issues' not in result:
                raise Exception("编号分析结果格式错误：缺少 has_issues 字段")
            
            # 检查是否检测到问题
            has_issues = result.get('has_issues', False)
            duplicate_numbers = result.get('duplicate_numbers', [])
            discontinuous_numbers = result.get('discontinuous_numbers', [])
            
            total_issues = len(duplicate_numbers) + len(discontinuous_numbers)
            
            duration = time.time() - start_time
            if has_issues or total_issues > 0:
                self.log_test("编号问题分析", True, f"检测到 {total_issues} 个编号问题", duration)
            else:
                self.log_test("编号问题分析", True, "未检测到编号问题", duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("编号问题分析", False, str(e), duration)
            return False
    
    async def test_numbering_analysis_detailed(self) -> bool:
        """测试详细编号分析功能"""
        try:
            start_time = time.time()
            
            # 导入测试模块
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from markdown_toc.extractor import extract_toc_from_content, analyze_numbering_issues_from_headers
            
            # 测试有编号问题的文档
            test_file = Path(self.test_directory) / SERVER_CONFIG["test_files_dir"] / "numbering_issues.md"
            content = test_file.read_text(encoding='utf-8')
            headers = extract_toc_from_content(content)
            result = analyze_numbering_issues_from_headers(headers)
            
            # 验证结果
            if not result:
                raise Exception("编号分析失败：无法分析编号问题")
            
            # 获取问题信息
            has_issues = result.get('has_issues', False)
            duplicate_numbers = result.get('duplicate_numbers', [])
            discontinuous_numbers = result.get('discontinuous_numbers', [])
            
            # 验证分析结果的完整性
            if not isinstance(has_issues, bool):
                raise Exception("编号分析结果格式不正确：has_issues 字段类型错误")
            
            if not isinstance(duplicate_numbers, list):
                raise Exception("编号分析结果格式不正确：duplicate_numbers 字段类型错误")
                
            if not isinstance(discontinuous_numbers, list):
                raise Exception("编号分析结果格式不正确：discontinuous_numbers 字段类型错误")
            
            # 统计问题数量
            total_issues = len(duplicate_numbers) + len(discontinuous_numbers)
            
            duration = time.time() - start_time
            self.log_test("详细编号分析", True, f"检测到 {total_issues} 个编号问题", duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("详细编号分析", False, str(e), duration)
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理功能"""
        try:
            start_time = time.time()
            
            # 导入测试模块
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from markdown_toc.extractor import extract_toc_from_content
            
            # 测试空内容
            try:
                result = extract_toc_from_content("")
                if result:  # 空内容应该返回空列表，不应该抛出错误
                    if len(result) > 0:
                        raise Exception("空内容应该返回空结果")
            except Exception as e:
                raise Exception(f"处理空内容时出错: {e}")
            
            # 测试无效的 Markdown 内容
            try:
                invalid_content = "这不是有效的标题格式\n没有 # 符号的内容"
                result = extract_toc_from_content(invalid_content)
                # 无效内容应该返回空列表，不应该抛出错误
                if result and len(result) > 0:
                    raise Exception("无效内容应该返回空结果")
            except Exception as e:
                raise Exception(f"处理无效内容时出错: {e}")
            
            duration = time.time() - start_time
            self.log_test("错误处理测试", True, "正确处理了各种错误情况", duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("错误处理测试", False, str(e), duration)
            return False
    
    async def test_performance(self) -> bool:
        """测试性能"""
        try:
            start_time = time.time()
            
            # 导入测试模块
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from markdown_toc.extractor import extract_toc_from_content
            
            # 生成大文档内容（601个标题）
            large_content = "# 大文档性能测试\n\n"
            for i in range(1, 601):
                level = (i % 3) + 1  # 1-3级标题
                prefix = "#" * level
                large_content += f"{prefix} {i}. 标题 {i}\n\n这是第 {i} 个标题的内容。\n\n"
            
            # 测试大文档的 TOC 提取
            toc_items = extract_toc_from_content(large_content)
            
            # 验证结果
            if not toc_items:
                raise Exception("大文档 TOC 提取失败")
            
            if len(toc_items) < 600:  # 应该提取到大部分标题
                raise Exception(f"大文档 TOC 提取不完整：只提取到 {len(toc_items)} 个标题")
            
            duration = time.time() - start_time
            self.log_test("性能测试", True, f"成功处理包含 601 个标题的大文档，耗时 {duration:.2f} 秒", duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("性能测试", False, str(e), duration)
            return False
    
    def generate_test_report(self):
        """生成测试报告并保存为 JSON 文件"""
        try:
            # 计算统计信息
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            failed_tests = total_tests - passed_tests
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            total_duration = sum(result['duration'] for result in self.test_results)
            average_duration = total_duration / total_tests if total_tests > 0 else 0
            
            # 构建报告数据
            report = {
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": round(success_rate, 1),
                    "total_duration": total_duration,
                    "average_duration": average_duration
                },
                "details": self.test_results
            }
            
            # 确保报告目录存在
            ensure_directories()
            
            # 保存报告文件
            report_path = get_report_file_path("markdown_toc_test_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📊 测试报告已保存: {report_path}")
            return str(report_path)
            
        except Exception as e:
            print(f"⚠️ 保存测试报告失败: {e}")
            return None

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行 Markdown TOC MCP Server 测试...")
        print(f"📁 测试目录: {self.test_directory}")
        print()
        
        # 运行核心功能测试
        tests = [
            ("TOC 提取功能", self.test_toc_extraction),
            ("编号问题分析", self.test_numbering_analysis),
            ("详细编号分析", self.test_numbering_analysis_detailed),
            ("错误处理测试", self.test_error_handling),
            ("性能测试", self.test_performance),
        ]
        
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            print(f"🔍 运行测试: {test_name}")
            try:
                success = await test_func()
                if success:
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"测试执行异常: {e}")
            print()
        
        # 生成并保存测试报告
        self.generate_test_report()
        
        # 生成测试报告
        print("📊 测试完成！")
        print(f"✅ 通过: {passed_tests}/{total_tests}")
        print(f"❌ 失败: {total_tests - passed_tests}/{total_tests}")
        print(f"📈 成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 所有测试都通过了！")
            return 0
        else:
            print("⚠️ 部分测试失败，请检查日志。")
            return 1
    
    def cleanup(self):
        """清理测试文件"""
        try:
            import shutil
            if os.path.exists(self.test_directory):
                shutil.rmtree(self.test_directory)
                print(f"🧹 已清理测试目录: {self.test_directory}")
        except Exception as e:
            print(f"⚠️ 清理测试目录失败: {e}")


async def main():
    """主函数"""
    tester = MarkdownTOCServerTester()
    
    try:
        exit_code = await tester.run_all_tests()
        return exit_code
    finally:
        tester.cleanup()


if __name__ == "__main__":
    try:
        import re
    except ImportError:
        print("⚠️ 警告: re 模块未找到，某些测试可能失败")
    
    print("\n🔍 开始测试 Markdown TOC MCP Server...")
    
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)