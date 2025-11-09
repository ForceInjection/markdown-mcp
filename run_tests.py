#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一测试运行脚本

本脚本用于运行项目中的所有测试，支持新的目录结构：
- tests/toc/        TOC 相关测试
- tests/editor/     编辑器相关测试
- tests/            其他通用测试

使用方法：
    python run_tests.py [选项]

选项：
    --all           运行所有测试 (默认)
    --toc           只运行 TOC 相关测试
    --editor        只运行编辑器相关测试
    --other         只运行其他通用测试
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


def run_test_file(test_file, subdir='', verbose=False):
    """运行单个测试文件"""
    if subdir:
        test_path = os.path.join('tests', subdir, test_file)
    else:
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
    parser.add_argument('--toc', action='store_true', help='只运行 TOC 相关测试')
    parser.add_argument('--editor', action='store_true', help='只运行编辑器相关测试')
    parser.add_argument('--other', action='store_true', help='只运行其他通用测试')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--report', '-r', action='store_true', help='生成测试报告')
    
    args = parser.parse_args()
    
    # 确定要运行的测试
    test_groups = []
    
    if args.toc:
        test_groups.append(('toc', [
            'test_extractor.py',
            'test_generate_toc.py',
            'test_chapter_extraction.py'
        ]))
    elif args.editor:
        test_groups.append(('editor', [
            'test_semantic_editor.py',
            'test_complex_document_integration.py'
        ]))
        test_groups.append(('', [
            'test_editor_mcp_server.py'  # 编辑器服务器测试位于根目录
        ]))
    elif args.other:
        test_groups.append(('', [
            'test_config.py',
            'test_toc_mcp_server.py'
        ]))
    else:
        # 默认运行所有测试
        test_groups = [
            ('toc', [
                'test_extractor.py',
                'test_generate_toc.py',
                'test_chapter_extraction.py',
                'test_comprehensive.py',
                'test_consistency.py',
                'test_edge_cases.py',
                'test_yarn_integration.py'  # 移动到正确的 TOC 组
            ]),
            ('editor', [
                'test_semantic_editor.py',
                'test_complex_document_integration.py'
            ]),
            ('', [
                'test_config.py',
                'test_toc_mcp_server.py',    # 添加 TOC 服务器测试
                'test_editor_mcp_server.py'  # 添加编辑器服务器测试
            ])
        ]
    
    # 计算总测试文件数
    total_test_files = sum(len(files) for _, files in test_groups)
    
    print("Markdown TOC 项目测试套件")
    print("=" * 50)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试组数: {len(test_groups)}")
    print(f"测试文件数: {total_test_files}")
    print("=" * 50)
    
    # 运行测试
    results = {}
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    total_duration = 0
    
    for subdir, test_files in test_groups:
        if subdir:
            print(f"\n📁 运行 {subdir.upper()} 测试组:")
        else:
            print(f"\n📁 运行通用测试组:")
        
        for test_file in test_files:
            success, details = run_test_file(test_file, subdir, args.verbose)
            results[test_file] = {
                'success': success,
                'details': details,
                'group': subdir or 'general'
            }
            
            total_tests += 1
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