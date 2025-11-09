#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数一致性测试

本测试文件专门用于验证以下三个核心文件之间的参数一致性：
1. extractor.py - 核心实现
2. toc_mcp_server.py - MCP 服务器接口
3. trae_mcp_config.json - 工具配置

测试内容：
- 参数定义一致性
- 默认值一致性
- 类型定义一致性
- 功能验证测试
"""

import json
import sys
import os
import tempfile
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
# 添加 tests 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from markdown_toc.extractor import MarkdownTOCExtractor
from test_config import TEST_CONFIG, get_test_file_path, get_report_file_path, ensure_directories


class ConsistencyTester:
    """参数一致性测试器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.extractor = MarkdownTOCExtractor()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "message": message
        })
        
        return success

    def load_config_file(self):
        """加载配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'trae_mcp_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 无法加载配置文件: {e}")
            return None

    def test_extract_toc_parameters(self):
        """测试 extract_toc 方法的参数一致性"""
        print("\n=== 测试 1: extract_toc 参数一致性 ===")
        
        # 创建测试内容
        test_content = """# 1. 第一章
## 1.1 第一节
### 1.1.1 子节
#### 1.1.1.1 深层子节
##### 1.1.1.1.1 更深层子节
###### 1.1.1.1.1.1 最深层子节
## 1.2 第二节
# 2. 第二章
## 2.1 第一节
"""
        
        success_count = 0
        total_tests = 0
        
        # 测试 min_depth 参数
        total_tests += 1
        try:
            headers = self.extractor.extract_toc(test_content, min_depth=2)
            # 应该只包含 level >= 2 的标题
            min_level = min(h['level'] for h in headers) if headers else 0
            if min_level >= 2:
                success_count += 1
                self.log_test("min_depth=2 参数功能", True, f"最小级别: {min_level}")
            else:
                self.log_test("min_depth=2 参数功能", False, f"期望最小级别>=2，实际: {min_level}")
        except Exception as e:
            self.log_test("min_depth=2 参数功能", False, f"异常: {e}")
        
        # 测试 max_depth 参数
        total_tests += 1
        try:
            headers = self.extractor.extract_toc(test_content, max_depth=3)
            # 应该只包含 level <= 3 的标题
            max_level = max(h['level'] for h in headers) if headers else 0
            if max_level <= 3:
                success_count += 1
                self.log_test("max_depth=3 参数功能", True, f"最大级别: {max_level}")
            else:
                self.log_test("max_depth=3 参数功能", False, f"期望最大级别<=3，实际: {max_level}")
        except Exception as e:
            self.log_test("max_depth=3 参数功能", False, f"异常: {e}")
        
        # 测试 include_line_numbers 参数
        total_tests += 1
        try:
            headers_with_lines = self.extractor.extract_toc(test_content, include_line_numbers=True)
            headers_without_lines = self.extractor.extract_toc(test_content, include_line_numbers=False)
            
            has_line_numbers = all('line_number' in h for h in headers_with_lines)
            no_line_numbers = all('line_number' not in h for h in headers_without_lines)
            
            if has_line_numbers and no_line_numbers:
                success_count += 1
                self.log_test("include_line_numbers 参数功能", True, "行号包含/排除正常")
            else:
                self.log_test("include_line_numbers 参数功能", False, 
                            f"行号功能异常: 包含={has_line_numbers}, 排除={no_line_numbers}")
        except Exception as e:
            self.log_test("include_line_numbers 参数功能", False, f"异常: {e}")
        
        return self.log_test("extract_toc 参数一致性测试", success_count == total_tests, 
                           f"通过 {success_count}/{total_tests} 项测试")

    def test_generate_toc_parameters(self):
        """测试 generate_toc 方法的参数一致性"""
        print("\n=== 测试 2: generate_toc 参数一致性 ===")
        
        # 创建测试内容
        test_content = """# 1. 第一章
## 1.1 第一节
### 1.1.1 子节
#### 1.1.1.1 深层子节
##### 1.1.1.1.1 更深层子节
###### 1.1.1.1.1.1 最深层子节
## 1.2 第二节
# 2. 第二章
## 2.1 第一节
"""
        
        success_count = 0
        total_tests = 0
        
        # 首先提取标题
        headers = self.extractor.extract_toc(test_content)
        
        # 测试默认 max_level=6
        total_tests += 1
        try:
            result = self.extractor.generate_toc(headers)
            if 'content' in result and 'format' in result:
                success_count += 1
                self.log_test("generate_toc 默认参数", True, f"生成了 {result.get('total_items', 0)} 项")
            else:
                self.log_test("generate_toc 默认参数", False, "返回结构不正确")
        except Exception as e:
            self.log_test("generate_toc 默认参数", False, f"异常: {e}")
        
        # 测试 max_level 参数
        total_tests += 1
        try:
            result = self.extractor.generate_toc(headers, max_level=3)
            if 'levels_included' in result:
                max_included_level = max(result['levels_included']) if result['levels_included'] else 0
                if max_included_level <= 3:
                    success_count += 1
                    self.log_test("max_level=3 参数功能", True, f"最大包含级别: {max_included_level}")
                else:
                    self.log_test("max_level=3 参数功能", False, f"期望最大级别<=3，实际: {max_included_level}")
            else:
                self.log_test("max_level=3 参数功能", False, "缺少 levels_included 字段")
        except Exception as e:
            self.log_test("max_level=3 参数功能", False, f"异常: {e}")
        
        # 测试不同格式
        total_tests += 1
        try:
            formats = ['markdown', 'html', 'text']
            format_success = 0
            for fmt in formats:
                result = self.extractor.generate_toc(headers, format_type=fmt)
                if result.get('format') == fmt and 'content' in result:
                    format_success += 1
            
            if format_success == len(formats):
                success_count += 1
                self.log_test("format_type 参数功能", True, f"支持 {format_success} 种格式")
            else:
                self.log_test("format_type 参数功能", False, f"仅支持 {format_success}/{len(formats)} 种格式")
        except Exception as e:
            self.log_test("format_type 参数功能", False, f"异常: {e}")
        
        return self.log_test("generate_toc 参数一致性测试", success_count == total_tests, 
                           f"通过 {success_count}/{total_tests} 项测试")

    def test_analyze_numbering_parameters(self):
        """测试 analyze_numbering_issues 方法的参数一致性"""
        print("\n=== 测试 3: analyze_numbering_issues 参数一致性 ===")
        
        # 创建包含编号问题的测试内容
        test_content = """# 1. 第一章
## 1.1 第一节
## 1.1 重复的第一节
## 1.3 跳过了1.2
# 2. 第二章
## 2.1 第一节
## 2.1 重复的第一节
# 4. 跳过了第三章
## 4.1 第一节
"""
        
        success_count = 0
        total_tests = 0
        
        # 首先提取标题
        headers = self.extractor.extract_toc(test_content)
        
        # 测试默认 check_types
        total_tests += 1
        try:
            result = self.extractor.analyze_numbering_issues(headers)
            if 'duplicate_numbers' in result and 'discontinuous_numbers' in result:
                success_count += 1
                self.log_test("analyze_numbering_issues 默认参数", True, 
                            f"发现重复: {len(result['duplicate_numbers'])}, 不连续: {len(result['discontinuous_numbers'])}")
            else:
                self.log_test("analyze_numbering_issues 默认参数", False, "返回结构不正确")
        except Exception as e:
            self.log_test("analyze_numbering_issues 默认参数", False, f"异常: {e}")
        
        # 测试只检查重复编号
        total_tests += 1
        try:
            result = self.extractor.analyze_numbering_issues(headers, check_types=['duplicates'])
            if 'duplicate_numbers' in result and len(result['duplicate_numbers']) > 0:
                success_count += 1
                self.log_test("check_types=['duplicates'] 参数功能", True, 
                            f"发现 {len(result['duplicate_numbers'])} 个重复编号")
            else:
                self.log_test("check_types=['duplicates'] 参数功能", False, "未正确检测重复编号")
        except Exception as e:
            self.log_test("check_types=['duplicates'] 参数功能", False, f"异常: {e}")
        
        # 测试只检查不连续编号
        total_tests += 1
        try:
            result = self.extractor.analyze_numbering_issues(headers, check_types=['discontinuous'])
            if 'discontinuous_numbers' in result and len(result['discontinuous_numbers']) > 0:
                success_count += 1
                self.log_test("check_types=['discontinuous'] 参数功能", True, 
                            f"发现 {len(result['discontinuous_numbers'])} 个不连续编号")
            else:
                self.log_test("check_types=['discontinuous'] 参数功能", False, "未正确检测不连续编号")
        except Exception as e:
            self.log_test("check_types=['discontinuous'] 参数功能", False, f"异常: {e}")
        
        return self.log_test("analyze_numbering_issues 参数一致性测试", success_count == total_tests, 
                           f"通过 {success_count}/{total_tests} 项测试")

    def test_config_consistency(self):
        """测试配置文件中的参数一致性"""
        print("\n=== 测试 4: 配置文件参数一致性 ===")
        
        config = self.load_config_file()
        if not config:
            return False
        
        success_count = 0
        total_tests = 0
        
        # 检查 extract_markdown_toc 工具配置
        total_tests += 1
        tools = config.get('tools', {})
        extract_tool = tools.get('extract_markdown_toc')
        
        if extract_tool:
            params = extract_tool.get('parameters', {})
            expected_params = ['file_path', 'output_format', 'min_depth', 'max_depth', 'include_line_numbers']
            has_all_params = all(param in params for param in expected_params)
            
            if has_all_params:
                success_count += 1
                self.log_test("extract_markdown_toc 配置参数", True, f"包含所有 {len(expected_params)} 个参数")
            else:
                missing = [p for p in expected_params if p not in params]
                self.log_test("extract_markdown_toc 配置参数", False, f"缺少参数: {missing}")
        else:
            self.log_test("extract_markdown_toc 配置参数", False, "未找到工具配置")
        
        # 检查 generate_toc 工具配置
        total_tests += 1
        generate_tool = tools.get('generate_toc')
        
        if generate_tool:
            params = generate_tool.get('parameters', {})
            max_level_param = params.get('max_level', {})
            
            # 检查 max_level 默认值是否为 6
            if max_level_param.get('default') == 6:
                success_count += 1
                self.log_test("generate_toc max_level 默认值", True, "默认值为 6")
            else:
                self.log_test("generate_toc max_level 默认值", False, 
                            f"期望默认值 6，实际: {max_level_param.get('default')}")
        else:
            self.log_test("generate_toc max_level 默认值", False, "未找到工具配置")
        
        # 检查 analyze_numbering_issues 工具配置
        total_tests += 1
        analyze_tool = tools.get('analyze_numbering_issues')
        
        if analyze_tool:
            params = analyze_tool.get('parameters', {})
            check_types_param = params.get('check_types', {})
            
            # 检查 check_types 枚举值 (在 items.enum 中)
            items = check_types_param.get('items', {})
            enum_values = items.get('enum', [])
            expected_enums = ['duplicates', 'discontinuous']
            has_correct_enums = all(enum in enum_values for enum in expected_enums)
            
            if has_correct_enums:
                success_count += 1
                self.log_test("analyze_numbering_issues check_types 枚举", True, f"包含: {enum_values}")
            else:
                self.log_test("analyze_numbering_issues check_types 枚举", False, 
                            f"期望: {expected_enums}，实际: {enum_values}")
        else:
            self.log_test("analyze_numbering_issues check_types 枚举", False, "未找到工具配置")
        
        return self.log_test("配置文件参数一致性测试", success_count == total_tests, 
                           f"通过 {success_count}/{total_tests} 项测试")

    def test_parameter_type_consistency(self):
        """测试参数类型一致性"""
        print("\n=== 测试 5: 参数类型一致性 ===")
        
        config = self.load_config_file()
        if not config:
            return False
        
        success_count = 0
        total_tests = 0
        
        # 检查整数类型参数的一致性
        total_tests += 1
        integer_params = ['min_depth', 'max_depth', 'max_level']
        type_consistency = True
        
        tools = config.get('tools', {})
        for tool_name, tool_config in tools.items():
            params = tool_config.get('parameters', {})
            for param_name in integer_params:
                if param_name in params:
                    param_type = params[param_name].get('type')
                    if param_type != 'integer':
                        type_consistency = False
                        self.log_test(f"{tool_name} {param_name} 类型", False, 
                                    f"期望 integer，实际: {param_type}")
        
        if type_consistency:
            success_count += 1
            self.log_test("整数参数类型一致性", True, "所有整数参数类型正确")
        
        return self.log_test("参数类型一致性测试", success_count == total_tests, 
                           f"通过 {success_count}/{total_tests} 项测试")

    def run_all_tests(self):
        """运行所有一致性测试"""
        print("🔍 开始参数一致性测试...")
        print("=" * 50)
        
        test_methods = [
            self.test_extract_toc_parameters,
            self.test_generate_toc_parameters,
            self.test_analyze_numbering_parameters,
            self.test_config_consistency,
            self.test_parameter_type_consistency
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            if test_method():
                passed_tests += 1
        
        print("\n" + "=" * 50)
        print("📊 测试总结")
        print("=" * 50)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {total_tests - passed_tests}")
        print(f"成功率: {(passed_tests / total_tests * 100):.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 所有参数一致性测试通过！")
            return 0
        else:
            print("⚠️ 部分测试失败，请检查参数一致性")
            return 1


def main():
    """主函数"""
    tester = ConsistencyTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    exit(main())