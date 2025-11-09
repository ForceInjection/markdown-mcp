#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件

本文件定义了测试环境的配置参数和常量。
"""

import os

# 测试环境配置
TEST_CONFIG = {
    # 基础路径配置
    "base_dir": os.path.dirname(os.path.abspath(__file__)),
    "project_root": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures"),
    "reports_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "reports"),
    
    # 测试文件配置
    "test_files": {
        "yarn_md": "yarn.md",
        "test_doc_md": "test_doc.md",
        "sample_md": "sample.md"
    },
    
    # 性能测试配置
    "performance": {
        "max_extraction_time": 5.0,  # 秒
        "max_analysis_time": 2.0,    # 秒
        "max_generation_time": 3.0,  # 秒
        "large_doc_headers": 6100,   # 大文档标题数量
        "large_doc_chapters": 100    # 大文档章节数量
    },
    
    # 测试数据配置
    "test_data": {
        # 标准测试内容
        "standard_content": """# 1. 项目介绍
## 1.1 项目背景
### 1.1.1 技术背景
### 1.1.2 业务背景
## 1.2 项目目标
# 2. 技术方案
## 2.1 架构设计
### 2.1.1 前端架构
### 2.1.2 后端架构
## 2.2 技术选型
""",
        
        # 重复编号测试内容
        "duplicate_content": """# 1. 第一章
## 1.1 第一节
## 1.1 重复的第一节
# 2. 第二章
## 2.1 第一节
## 2.1 重复的第一节
""",
        
        # 不连续编号测试内容
        "discontinuous_content": """# 1. 第一章
## 1.1 第一节
## 1.3 跳过了1.2
# 3. 跳过了第二章
## 3.1 第一节
""",
        
        # 汉字编号测试内容
        "chinese_content": """# 一、项目概述
## 一.一 项目背景
## 一.二 项目目标
# 二、技术方案
## 二.一 架构设计
## 二.二 技术选型
# 三、实施计划
""",
        
        # 混合编号测试内容
        "mixed_content": """# 1. 第一章
## 1.1 第一节
### 1.1.1 子节
# 二、第二章
## 2.1 第一节
# 3. 第三章
## 三.一 第一节
""",
        
        # 特殊字符测试内容
        "special_chars_content": """# 1. 标题包含特殊字符：@#$%^&*()
## 1.1 中英文混合 Title with English
### 1.1.1 数字123和符号！？
## 1.2 emoji 标题 🚀 📝 ✨
# 2. 另一个章节
""",
        
        # 深层嵌套测试内容
        "deep_nested_content": """# 1. 第一级
## 1.1 第二级
### 1.1.1 第三级
#### 1.1.1.1 第四级
##### 1.1.1.1.1 第五级
###### 1.1.1.1.1.1 第六级
"""
    },
    
    # 期望结果配置
    "expected_results": {
        "standard_headers_count": 9,
        "duplicate_headers_count": 6,
        "discontinuous_headers_count": 5,
        "chinese_headers_count": 7,
        "mixed_headers_count": 7,
        "special_chars_headers_count": 5,
        "deep_nested_headers_count": 6,
        "deep_nested_levels": [1, 2, 3, 4, 5, 6]
    },
    
    # 输出格式配置
    "output_formats": ["markdown", "html", "text"],
    
    # 测试超时配置
    "timeouts": {
        "default": 30,      # 秒
        "performance": 60,  # 秒
        "integration": 120  # 秒
    }
}

# 测试用例类别
TEST_CATEGORIES = {
    "core": "核心功能测试",
    "edge": "边界情况测试", 
    "server": "服务器功能测试",
    "integration": "集成测试",
    "comprehensive": "综合功能测试",
    "performance": "性能测试",
    "chinese": "汉字编号测试",
    "numbering": "编号分析测试",
    "toc_generation": "TOC 生成测试"
}

# 测试状态常量
TEST_STATUS = {
    "PASSED": "✓ 正常",
    "FAILED": "✗ 失败",
    "SKIPPED": "⚠ 跳过",
    "ERROR": "❌ 错误"
}

# 日志级别
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}


def get_test_file_path(filename):
    """获取测试文件的完整路径"""
    return os.path.join(TEST_CONFIG["fixtures_dir"], filename)


def get_report_file_path(filename):
    """获取报告文件的完整路径"""
    return os.path.join(TEST_CONFIG["reports_dir"], filename)


def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        TEST_CONFIG["fixtures_dir"],
        TEST_CONFIG["reports_dir"]
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_performance_limits():
    """获取性能测试限制"""
    return TEST_CONFIG["performance"]


def get_test_data(key):
    """获取测试数据"""
    # 首先尝试从文件中读取
    file_mapping = {
        "standard_content": "standard_content.md",
        "duplicate_content": "duplicate_content.md",
        "discontinuous_content": "discontinuous_content.md",
        "chinese_content": "chinese_content.md",
        "mixed_content": "mixed_content.md",
        "special_chars_content": "special_chars_content.md",
        "deep_nested_content": "deep_nested_content.md"
    }
    
    if key in file_mapping:
        file_path = get_test_file_path(file_mapping[key])
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Failed to read test data from {file_path}: {e}")
    
    # 如果文件不存在或读取失败，返回硬编码的备份数据
    return TEST_CONFIG["test_data"].get(key, "")


def get_expected_result(key):
    """获取期望结果"""
    return TEST_CONFIG["expected_results"].get(key, 0)


# 初始化测试环境
def init_test_environment():
    """初始化测试环境"""
    ensure_directories()
    
    # 创建示例测试文件（如果不存在）
    sample_file = get_test_file_path("sample.md")
    if not os.path.exists(sample_file):
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(get_test_data("standard_content"))
    
    return True


if __name__ == "__main__":
    # 测试配置
    print("测试配置信息:")
    print(f"项目根目录: {TEST_CONFIG['project_root']}")
    print(f"测试基础目录: {TEST_CONFIG['base_dir']}")
    print(f"测试数据目录: {TEST_CONFIG['fixtures_dir']}")
    print(f"报告目录: {TEST_CONFIG['reports_dir']}")
    
    # 初始化环境
    if init_test_environment():
        print("✅ 测试环境初始化成功")
    else:
        print("❌ 测试环境初始化失败")