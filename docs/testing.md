# 测试文档

本文档描述了 Markdown TOC 项目的测试结构、测试用例和使用方法。

## 1. 测试结构

### 1.1 测试目录结构

```text
markdown-mcp/
├── tests/                          # 测试目录
│   ├── __init__.py                 # 包初始化文件
│   ├── test_config.py              # 测试配置文件
│   ├── test_extractor.py           # 核心功能测试
│   ├── test_edge_cases.py          # 边界情况测试
│   ├── test_server.py              # 服务器功能测试
│   ├── test_yarn_integration.py    # 集成测试
│   ├── test_comprehensive.py       # 综合功能测试
│   ├── test_generate_toc.py        # TOC 生成功能测试
│   ├── test_consistency.py         # 参数一致性测试
│   └── fixtures/                   # 测试数据文件
│       └── yarn.md                 # YARN 文档测试数据
├── run_tests.py                    # 统一测试运行脚本
└── docs/
    └── testing.md                  # 本文档
```

### 1.2 测试文件说明

| 测试文件                   | 功能描述       | 测试内容                                                                  |
| -------------------------- | -------------- | ------------------------------------------------------------------------- |
| `test_config.py`           | 测试配置文件   | 测试环境配置参数、常量定义、路径配置、性能配置、测试数据                  |
| `test_extractor.py`        | 核心功能测试   | TOC 提取、编号分析、TOC 生成、汉字编号识别、便利函数、has_issues 含义验证 |
| `test_edge_cases.py`       | 边界情况测试   | 空文件、特殊字符、极大文件、格式错误、复杂嵌套、多语言混合、内存使用      |
| `test_server.py`           | 服务器功能测试 | MCP 服务器的 TOC 提取、编号分析、详细编号分析、错误处理、性能测试         |
| `test_yarn_integration.py` | 集成测试       | 基于 yarn.md 的复杂文档处理、中英文混合内容、代码块处理、性能测试         |
| `test_comprehensive.py`    | 综合功能测试   | TOC 生成格式（Markdown、HTML、Text）、YARN 文档处理、健壮性、性能内存测试 |
| `test_generate_toc.py`     | TOC 生成测试   | 基本 TOC 生成、多格式输出、参数配置、性能测试、README 文件处理            |
| `test_consistency.py`      | 参数一致性测试 | 核心文件间参数一致性、默认值一致性、类型定义一致性、配置文件一致性验证    |

---

## 2. 测试用例分类

### 2.1 核心功能测试

#### 2.1.1 TOC 提取测试

- **目标**：验证标题提取的准确性
- **测试内容**：
  - 多级标题提取
  - 标题层级识别
  - 行号记录
  - 标题内容解析

#### 2.1.2 编号分析测试

- **目标**：验证编号问题检测功能
- **测试内容**：
  - 重复编号检测
  - 不连续编号检测
  - 编号统计分析
  - has_issues 状态判断

#### 2.1.3 TOC 生成测试

- **目标**：验证 TOC 生成的正确性
- **测试内容**：
  - Markdown 格式生成
  - HTML 格式生成
  - 文本格式生成
  - 生成结果验证

#### 2.1.4 汉字编号测试

- **目标**：验证汉字数字识别功能
- **测试内容**：
  - 基础汉字数字（一、二、三）
  - 复合汉字数字（十一、二十）
  - 繁体汉字数字
  - 无效输入处理

#### 2.1.5 便利函数测试

- **目标**：验证便利函数的功能
- **测试内容**：
  - extract_and_analyze 函数
  - 返回结果结构验证
  - 错误处理

#### 2.1.6 has_issues 含义测试

- **目标**：验证 has_issues 返回值的正确性
- **测试内容**：
  - 正常编号文档（has_issues: False）
  - 重复编号文档（has_issues: True）
  - 不连续编号文档（has_issues: True）

### 2.2 边界情况测试

#### 2.2.1 空内容处理

- 空字符串
- 只有空白字符
- 只有换行符

#### 2.2.2 特殊字符处理

- 特殊符号标题
- emoji 表情符号
- 中英文混合
- 数字和符号组合

#### 2.2.3 极端情况

- 极大文档（6000+ 标题）
- 深层嵌套（6 级标题）
- 格式错误的标题

#### 2.2.4 多语言支持

- 中文标题
- 英文标题
- 中英文混合
- 其他语言字符

### 2.3 性能测试

#### 2.3.1 性能指标

- **提取性能**：< 5.0 秒（6000+ 标题）
- **分析性能**：< 2.0 秒
- **生成性能**：< 3.0 秒

#### 2.3.2 内存使用

- 大文档处理时的内存占用
- 内存泄漏检测

---

## 3. 使用方法

### 3.1 运行所有测试

```bash
# 运行所有测试（默认）
python run_tests.py
python run_tests.py --all

# 运行所有测试并生成报告
python run_tests.py --report

# 详细输出模式
python run_tests.py --verbose
python run_tests.py -v

# 同时使用详细输出和生成报告
python run_tests.py --verbose --report
python run_tests.py -v -r
```

### 3.2 运行特定测试

```bash
# 只运行核心功能测试
python run_tests.py --core

# 只运行边界情况测试
python run_tests.py --edge

# 只运行服务器测试
python run_tests.py --server

# 只运行集成测试
python run_tests.py --integration

# 只运行综合测试
python run_tests.py --comprehensive

# 只运行参数一致性测试
python run_tests.py --consistency

# 只运行 TOC 生成功能测试
python run_tests.py --generate-toc
```

### 3.3 运行单个测试文件

```bash
# 运行测试配置文件
python tests/test_config.py

# 运行核心功能测试
python tests/test_extractor.py

# 运行边界情况测试
python tests/test_edge_cases.py

# 运行服务器功能测试
python tests/test_server.py

# 运行集成测试
python tests/test_yarn_integration.py

# 运行综合功能测试
python tests/test_comprehensive.py

# 运行 TOC 生成功能测试
python tests/test_generate_toc.py

# 运行参数一致性测试
python tests/test_consistency.py
```

---

## 4. 测试配置

### 4.1 配置文件

测试配置定义在 `tests/test_config.py` 中，包括：

- **路径配置**：基础目录、项目根目录、fixtures 目录、报告目录
- **性能配置**：提取时间限制（5.0s）、分析时间限制（2.0s）、生成时间限制（3.0s）
- **测试数据**：标准测试内容、重复编号内容、不连续编号内容、汉字编号内容、混合编号内容、特殊字符内容、深层嵌套内容
- **期望结果**：各种测试内容的预期标题数量和层级
- **输出格式**：支持 markdown、html、text 格式
- **超时配置**：默认超时（30s）、性能测试超时（60s）、集成测试超时（120s）

### 4.2 环境要求

- Python 3.8+
- 项目依赖包已安装（参考 `requirements.txt`）
- 测试数据文件存在于 `tests/fixtures/` 目录

### 4.3 测试数据

测试使用的数据文件位于 `tests/fixtures/` 目录：

- `yarn.md`：复杂的真实文档，用于集成测试和综合功能验证

注：其他测试数据（如标准测试内容、重复编号内容等）直接定义在 `test_config.py` 的 `TEST_CONFIG["test_data"]` 中。

## 5. 测试报告

### 5.1 报告格式

测试报告以 JSON 格式保存在 `tests/reports/` 目录，包含：

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "summary": {
    "total_tests": 5,
    "passed_tests": 5,
    "failed_tests": 0,
    "success_rate": 100.0,
    "total_duration": 15.23
  },
  "test_results": {
    "test_extractor.py": {
      "status": "PASSED",
      "details": {
        "duration": 3.45,
        "output": "..."
      }
    }
  }
}
```

### 5.2 报告类型

- **综合报告**：`run_tests.py --report` 生成的总体测试报告
- **单独报告**：各测试文件生成的专项报告
  - `core_functions_test_report.json`：核心功能测试报告
  - `edge_cases_test_report.json`：边界情况测试报告
  - `markdown_toc_test_report.json`：服务器功能测试报告
  - `yarn_integration_test_report.json`：集成测试报告
  - `comprehensive_test_report.json`：综合功能测试报告
  - `generate_toc_test_report.json`：TOC 生成功能测试报告

### 5.3 报告内容

- **测试总结**：总测试数、通过数、失败数、成功率、总耗时
- **详细结果**：每个测试文件的状态、耗时、输出信息
- **时间戳**：测试运行时间
- **测试环境**：Python 版本、系统信息等

---
