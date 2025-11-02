#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一测试运行脚本

本脚本用于运行项目中的所有测试，包括：
1. 核心功能测试 (test_extractor.py)
2. 边界情况测试 (test_edge_cases.py)
3. 服务器功能测试 (test_server.py)
4. 集成测试 (test_yarn_integration.py)
5. 综合功能测试 (test_comprehensive.py)
6. 参数一致性测试 (test_consistency.py)
7. TOC 生成功能测试 (test_generate_toc.py)

使用方法：
    python run_tests.py [选项]

选项：
    --all           运行所有测试 (默认)
    --core          只运行核心功能测试
    --edge          只运行边界情况测试
    --server        只运行服务器测试
    --integration   只运行集成测试
    --comprehensive 只运行综合测试
    --consistency   只运行参数一致性测试
    --generate-toc  只运行 TOC 生成功能测试
    --verbose       详细输出
    --report        生成测试报告
"""

import sys
import os
import argparse
import subprocess
import json
import time
from datetime import datetime

# 添加 tests 目录到 Python 路径以导入 test_config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
from test_config import TEST_CONFIG, get_report_file_path, ensure_directories


def run_test_file(test_file, verbose=False):
    """运行单个测试文件"""
    test_path = os.path.join('tests', test_file)
    
    if not os.path.exists(test_path):
        print(f"⚠️ 测试文件不存在: {test_path}")
        return False, f"文件不存在: {test_path}"
    
    print(f"🧪 运行测试: {test_file}")
    
    try:
        start_time = time.time()
        
        # 运行测试
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_file} 通过 ({duration:.2f}s)")
            if verbose and result.stdout:
                print(f"输出:\n{result.stdout}")
            return True, {"duration": duration, "output": result.stdout}
        else:
            print(f"❌ {test_file} 失败 ({duration:.2f}s)")
            if result.stderr:
                print(f"错误:\n{result.stderr}")
            if verbose and result.stdout:
                print(f"输出:\n{result.stdout}")
            return False, {"duration": duration, "error": result.stderr, "output": result.stdout}
            
    except Exception as e:
        print(f"❌ 运行 {test_file} 时发生异常: {e}")
        return False, f"异常: {e}"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行 Markdown TOC 项目测试')
    parser.add_argument('--all', action='store_true', default=True, help='运行所有测试')
    parser.add_argument('--core', action='store_true', help='只运行核心功能测试')
    parser.add_argument('--edge', action='store_true', help='只运行边界情况测试')
    parser.add_argument('--server', action='store_true', help='只运行服务器测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--comprehensive', action='store_true', help='只运行综合测试')
    parser.add_argument('--consistency', action='store_true', help='只运行一致性测试')
    parser.add_argument('--generate-toc', action='store_true', help='只运行 TOC 生成功能测试')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--report', '-r', action='store_true', help='生成测试报告')
    
    args = parser.parse_args()
    
    # 确定要运行的测试
    test_files = []
    
    if args.core:
        test_files.append('test_extractor.py')
    elif args.edge:
        test_files.append('test_edge_cases.py')
    elif args.server:
        test_files.append('test_server.py')
    elif args.integration:
        test_files.append('test_yarn_integration.py')
    elif args.comprehensive:
        test_files.append('test_comprehensive.py')
    elif args.consistency:
        test_files.append('test_consistency.py')
    elif getattr(args, 'generate_toc', False):
        test_files.append('test_generate_toc.py')
    else:
        # 默认运行所有测试
        test_files = [
            'test_extractor.py',
            'test_edge_cases.py',
            'test_server.py',
            'test_yarn_integration.py',
            'test_comprehensive.py',
            'test_consistency.py',
            'test_generate_toc.py'
        ]
    
    print("Markdown TOC 项目测试套件")
    print("=" * 50)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试文件数: {len(test_files)}")
    print("=" * 50)
    
    # 运行测试
    results = {}
    total_tests = len(test_files)
    passed_tests = 0
    failed_tests = 0
    total_duration = 0
    
    for test_file in test_files:
        success, details = run_test_file(test_file, args.verbose)
        results[test_file] = {
            'success': success,
            'details': details
        }
        
        if success:
            passed_tests += 1
            if isinstance(details, dict) and 'duration' in details:
                total_duration += details['duration']
        else:
            failed_tests += 1
    
    # 输出总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
    print(f"总耗时: {total_duration:.2f}s")
    
    if failed_tests > 0:
        print("\n失败的测试:")
        for test_file, result in results.items():
            if not result['success']:
                print(f"  ❌ {test_file}")
    
    # 生成测试报告
    if args.report:
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(passed_tests/total_tests*100, 1),
                "total_duration": round(total_duration, 2)
            },
            "test_results": {}
        }
        
        for test_file, result in results.items():
            report["test_results"][test_file] = {
                "status": "PASSED" if result['success'] else "FAILED",
                "details": result['details']
            }
        
        # 保存报告
        ensure_directories()
        report_file = get_report_file_path(f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 测试报告已保存到: {report_file}")
    
    print("=" * 50)
    
    # 返回适当的退出码
    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    exit(main())