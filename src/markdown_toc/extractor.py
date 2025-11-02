#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown TOC 核心功能模块

专注于三个核心功能：
1. TOC 提取 - 从 Markdown 内容中提取标题信息（包含行号）
2. 编号问题分析 - 检测重复编号和不连续编号问题
3. TOC 生成 - 生成格式化的 TOC 内容供插入文档

设计原则：
- 输入输出明确，便于 MCP Agent 调用
- 功能模块化，职责单一
- 无文件 I/O 依赖，纯内容处理
"""

import re
from typing import List, Dict, Any, Optional


class MarkdownTOCExtractor:
    """Markdown TOC 核心功能类"""
    
    def __init__(self):
        """初始化提取器"""
        pass
    
    def extract_toc(self, content: str, min_depth: int = 1, max_depth: int = 6, include_line_numbers: bool = True) -> List[Dict[str, Any]]:
        """
        从 Markdown 内容中提取 TOC 信息
        
        Args:
            content: Markdown 文档内容字符串
            min_depth: 最小标题深度 (1-6)，默认为 1
            max_depth: 最大标题深度 (1-6)，默认为 6
            include_line_numbers: 是否包含行号信息，默认为 True
            
        Returns:
            标题信息列表，每个元素包含：
            - level: 标题级别 (1-6)
            - title: 标题文本
            - line_number: 行号 (当 include_line_numbers=True 时)
            - raw_line: 原始行内容
            
        Example:
            >>> extractor = MarkdownTOCExtractor()
            >>> content = "# 标题1\\n## 标题2\\n### 标题3"
            >>> result = extractor.extract_toc(content, min_depth=2)
            >>> print(result[0])
            {'level': 2, 'title': '标题2', 'line_number': 2, 'raw_line': '## 标题2'}
        """
        # 参数验证
        if not (1 <= min_depth <= 6):
            raise ValueError("min_depth 必须在 1-6 之间")
        if not (1 <= max_depth <= 6):
            raise ValueError("max_depth 必须在 1-6 之间")
        if min_depth > max_depth:
            raise ValueError("min_depth 不能大于 max_depth")
        
        # 移除代码块中的内容，避免误识别
        cleaned_content = self._remove_code_blocks(content)
        
        # 提取标题信息
        headers = self._extract_headers(cleaned_content)
        
        # 按深度过滤
        filtered_headers = [
            h for h in headers 
            if min_depth <= h['level'] <= max_depth
        ]
        
        # 根据参数决定是否包含行号
        if not include_line_numbers:
            for header in filtered_headers:
                header.pop('line_number', None)
        
        return filtered_headers
    
    def analyze_numbering_issues(self, headers: List[Dict[str, Any]], check_types: List[str] = None) -> Dict[str, Any]:
        """
        分析标题编号问题
        
        Args:
            headers: 由 extract_toc 返回的标题信息列表
            check_types: 要执行的检查类型列表，可选值：
                - 'duplicates': 检查重复编号
                - 'discontinuous': 检查不连续编号
                - 'formats': 检查编号格式一致性（未来实现）
                - 'missing': 检查缺失编号（未来实现）
                默认为 ['duplicates', 'discontinuous']
            
        Returns:
            编号问题分析结果：
            - has_issues: 是否存在问题
            - duplicate_numbers: 重复编号列表（当 'duplicates' 在 check_types 中时）
            - discontinuous_numbers: 不连续编号信息（当 'discontinuous' 在 check_types 中时）
            - statistics: 统计信息
            
        Example:
            >>> headers = [
            ...     {'level': 1, 'title': '1. 介绍', 'line_number': 1},
            ...     {'level': 1, 'title': '1. 重复', 'line_number': 3},
            ...     {'level': 1, 'title': '3. 跳跃', 'line_number': 5}
            ... ]
            >>> result = extractor.analyze_numbering_issues(headers, ['duplicates'])
            >>> result['has_issues']
            True
        """
        # 设置默认检查类型
        if check_types is None:
            check_types = ['duplicates', 'discontinuous']
        
        # 验证检查类型
        valid_types = ['duplicates', 'discontinuous', 'formats', 'missing']
        for check_type in check_types:
            if check_type not in valid_types:
                raise ValueError(f"不支持的检查类型: {check_type}。支持的类型: {valid_types}")
        
        duplicate_numbers = []
        discontinuous_numbers = []
        
        # 按级别分组分析
        level_groups = {}
        for header in headers:
            level = header['level']
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(header)
        
        # 分析每个级别的编号
        for level, level_headers in level_groups.items():
            # 提取编号
            numbered_headers = []
            for header in level_headers:
                extracted_number = self._extract_number_from_title(header['title'], level)
                if extracted_number is not None:
                    numbered_headers.append({
                        'number': extracted_number,
                        'title': header['title'],
                        'line_number': header['line_number']
                    })
            
            if not numbered_headers:
                continue
                
            # 检测重复编号（仅当 'duplicates' 在 check_types 中时）
            if 'duplicates' in check_types:
                seen_numbers = {}
                for item in numbered_headers:
                    number = item['number']
                    if number in seen_numbers:
                        # 检查是否已经存在这个重复编号的记录
                        existing_duplicate = None
                        for dup in duplicate_numbers:
                            if dup['number'] == number and dup['level'] == level:
                                existing_duplicate = dup
                                break
                        
                        if existing_duplicate:
                            existing_duplicate['occurrences'].append(item)
                        else:
                            duplicate_numbers.append({
                                'number': number,
                                'level': level,
                                'occurrences': [seen_numbers[number], item]
                            })
                    else:
                        seen_numbers[number] = item
            
            # 检测不连续编号（仅当 'discontinuous' 在 check_types 中时）
            if 'discontinuous' in check_types:
                # 分别处理简单编号和多级编号
                simple_numbered_headers = []
                multilevel_groups = {}
                
                for item in numbered_headers:
                    number_str = item['number']
                    # 处理多级编号（如 4.1, 4.2）
                    if '.' in number_str:
                        parts = number_str.split('.')
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            prefix = parts[0]
                            suffix = int(parts[1])
                            if prefix not in multilevel_groups:
                                multilevel_groups[prefix] = []
                            multilevel_groups[prefix].append({
                                'number': suffix,
                                'title': item['title'],
                                'line_number': item['line_number']
                            })
                    # 处理简单数字编号
                    elif number_str.isdigit():
                        simple_numbered_headers.append({
                            'number': int(number_str),
                            'title': item['title'],
                            'line_number': item['line_number']
                        })
                
                # 检查简单编号的连续性
                if simple_numbered_headers:
                    numbers = sorted([item['number'] for item in simple_numbered_headers])
                    expected = 1
                    for number in numbers:
                        if number != expected:
                            discontinuous_numbers.append({
                                'level': level,
                                'expected': expected,
                                'actual': number,
                                'title': next(h['title'] for h in simple_numbered_headers if h['number'] == number),
                                'line_number': next(h['line_number'] for h in simple_numbered_headers if h['number'] == number)
                            })
                            expected = number + 1
                        else:
                            expected += 1
                
                # 检查多级编号的连续性（每个前缀组内部）
                for prefix, group_headers in multilevel_groups.items():
                    numbers = sorted([item['number'] for item in group_headers])
                    expected = 1
                    for number in numbers:
                        if number != expected:
                            discontinuous_numbers.append({
                                'level': level,
                                'expected': expected,
                                'actual': number,
                                'title': next(h['title'] for h in group_headers if h['number'] == number),
                                'line_number': next(h['line_number'] for h in group_headers if h['number'] == number)
                            })
                            expected = number + 1
                        else:
                            expected += 1
        
        # 统计信息
        total_headers = len(headers)
        numbered_headers_count = sum(
            len([h for h in level_headers if self._extract_number_from_title(h['title'], level) is not None])
            for level, level_headers in level_groups.items()
        )
        
        return {
            'has_issues': len(duplicate_numbers) > 0 or len(discontinuous_numbers) > 0,
            'duplicate_numbers': duplicate_numbers,
            'discontinuous_numbers': discontinuous_numbers,
            'statistics': {
                'total_headers': total_headers,
                'numbered_headers': numbered_headers_count,
                'levels_with_issues': len(set(
                    [item['level'] for item in duplicate_numbers] +
                    [item['level'] for item in discontinuous_numbers]
                ))
            }
        }
    
    def generate_toc(self, 
                     headers: List[Dict[str, Any]], 
                     format_type: str = 'markdown',
                     include_links: bool = False,
                     max_level: Optional[int] = 6) -> Dict[str, Any]:
        """
        生成格式化的 TOC 内容
        
        Args:
            headers: 由 extract_toc 返回的标题信息列表
            format_type: 输出格式 ('markdown', 'html', 'text')
            include_links: 是否包含链接（仅对 markdown 格式有效）
            max_level: 最大包含的标题级别
            
        Returns:
            生成的 TOC 信息：
            - content: 格式化的 TOC 内容
            - format: 使用的格式
            - total_items: 包含的条目数
            - levels_included: 包含的级别范围
            
        Example:
            >>> headers = [
            ...     {'level': 1, 'title': '介绍', 'line_number': 1},
            ...     {'level': 2, 'title': '概述', 'line_number': 3}
            ... ]
            >>> result = extractor.generate_toc(headers, 'markdown')
            >>> print(result['content'])
            - [介绍](#介绍)
              - [概述](#概述)
        """
        # 过滤级别
        filtered_headers = headers
        if max_level:
            filtered_headers = [h for h in headers if h['level'] <= max_level]
        
        if not filtered_headers:
            return {
                'content': '',
                'format': format_type,
                'total_items': 0,
                'levels_included': []
            }
        
        # 生成内容
        if format_type == 'markdown':
            content = self._generate_markdown_toc(filtered_headers, include_links)
        elif format_type == 'html':
            content = self._generate_html_toc(filtered_headers)
        elif format_type == 'text':
            content = self._generate_text_toc(filtered_headers)
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")
        
        # 统计信息
        levels_included = sorted(list(set(h['level'] for h in filtered_headers)))
        
        return {
            'content': content,
            'format': format_type,
            'total_items': len(filtered_headers),
            'levels_included': levels_included
        }
    
    def _remove_code_blocks(self, content: str) -> str:
        """移除代码块中的内容，但保留标题行"""
        lines = content.split('\n')
        result_lines = []
        in_triple_backtick_block = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # 处理三重反引号代码块
            if stripped_line.startswith('```'):
                in_triple_backtick_block = not in_triple_backtick_block
                continue
            
            # 如果在代码块内，跳过
            if in_triple_backtick_block:
                continue
            
            # 检查是否是标题行，如果是标题行则保留原样
            if re.match(r'^#{1,6}\s+', stripped_line):
                result_lines.append(line)
            else:
                # 非标题行才移除行内代码
                line_cleaned = re.sub(r'`[^`\n]*`', '', line)
                result_lines.append(line_cleaned)
        
        return '\n'.join(result_lines)
    
    def _extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """提取标题信息"""
        headers = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 匹配 Markdown 标题格式
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                
                # 清理标题文本
                title = self._clean_title_text(title)
                
                headers.append({
                    'level': level,
                    'title': title,
                    'line_number': line_num,
                    'raw_line': line.strip()
                })
        
        return headers
    
    def _chinese_number_to_int(self, chinese_num: str) -> Optional[int]:
        """将汉字数字转换为阿拉伯数字
        
        Args:
            chinese_num: 汉字数字字符串
            
        Returns:
            对应的阿拉伯数字，如果无法转换则返回 None
        """
        # 基础汉字数字映射
        chinese_digits = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '〇': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5,
            '陆': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10
        }
        
        # 处理简单的单个汉字数字
        if len(chinese_num) == 1 and chinese_num in chinese_digits:
            return chinese_digits[chinese_num]
        
        # 处理 "十X" 格式 (如 "十一", "十二")
        if chinese_num.startswith('十') and len(chinese_num) == 2:
            second_char = chinese_num[1]
            if second_char in chinese_digits:
                return 10 + chinese_digits[second_char]
        
        # 处理 "X十" 格式 (如 "二十", "三十")
        if chinese_num.endswith('十') and len(chinese_num) == 2:
            first_char = chinese_num[0]
            if first_char in chinese_digits:
                return chinese_digits[first_char] * 10
        
        # 处理 "X十Y" 格式 (如 "二十一", "三十五")
        if len(chinese_num) == 3 and chinese_num[1] == '十':
            first_char = chinese_num[0]
            third_char = chinese_num[2]
            if first_char in chinese_digits and third_char in chinese_digits:
                return chinese_digits[first_char] * 10 + chinese_digits[third_char]
        
        # 处理特殊情况 "十" (表示 10)
        if chinese_num == '十':
            return 10
        
        return None
    
    def _extract_number_from_title(self, title: str, level: int) -> Optional[str]:
        """从标题中提取编号（返回完整编号字符串），支持多种编号格式
        
        Args:
            title: 标题文本
            level: 标题级别
            
        Returns:
            提取到的完整编号字符串，如果没有找到则返回 None
        """
        # 1. 标准数字编号 (1.2.3)
        number_match = re.match(r'^(\d+(?:\.\d+)*)\.?\s*(.+)', title)
        if number_match:
            full_number = number_match.group(1)
            number_parts = full_number.split('.')
            # 更灵活的匹配条件：编号部分数量应该小于等于标题级别
            if len(number_parts) <= level and len(number_parts) > 0:
                return full_number
        
        # 2. 中文章节编号 (第 X 章/节/小节/部分) - 数字版本
        chapter_match = re.match(r'^第\s*(\d+)\s*(章|节|小节|部分)\s*(.+)', title)
        if chapter_match:
            return chapter_match.group(1)
        
        # 3. 中文章节编号 (第 X 章/节/小节/部分) - 汉字版本
        chinese_chapter_match = re.match(r'^第\s*([一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾〇零]+)\s*(章|节|小节|部分)\s*(.+)', title)
        if chinese_chapter_match:
            chinese_num = chinese_chapter_match.group(1)
            converted_num = self._chinese_number_to_int(chinese_num)
            if converted_num is not None:
                return str(converted_num)
        
        # 4. 汉字编号带顿号 (一、二、三、)
        chinese_with_comma_match = re.match(r'^([一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾〇零]+)、\s*(.+)', title)
        if chinese_with_comma_match:
            chinese_num = chinese_with_comma_match.group(1)
            converted_num = self._chinese_number_to_int(chinese_num)
            if converted_num is not None:
                return str(converted_num)
        
        # 5. 汉字编号带括号 ((一)、(二)、(三))
        chinese_with_parentheses_match = re.match(r'^\(([一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾〇零]+)\)\s*(.+)', title)
        if chinese_with_parentheses_match:
            chinese_num = chinese_with_parentheses_match.group(1)
            converted_num = self._chinese_number_to_int(chinese_num)
            if converted_num is not None:
                return str(converted_num)
        
        # 6. 纯汉字编号 (一 二 三)
        chinese_only_match = re.match(r'^([一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾〇零]+)\s+(.+)', title)
        if chinese_only_match:
            chinese_num = chinese_only_match.group(1)
            converted_num = self._chinese_number_to_int(chinese_num)
            if converted_num is not None:
                return str(converted_num)
        
        # 7. 其他可能的编号格式
        # 简单数字开头 (如 "1 介绍")
        simple_number_match = re.match(r'^(\d+)\s+(.+)', title)
        if simple_number_match:
            return simple_number_match.group(1)
        
        return None
    
    def _clean_title_text(self, title: str) -> str:
        """清理标题文本中的 Markdown 格式"""
        # 移除粗体
        title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)
        # 移除斜体
        title = re.sub(r'\*(.*?)\*', r'\1', title)
        # 移除行内代码
        title = re.sub(r'`(.*?)`', r'\1', title)
        # 移除链接，保留文本
        title = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', title)
        
        return title.strip()
    
    def _generate_markdown_toc(self, headers: List[Dict[str, Any]], include_links: bool) -> str:
        """生成 Markdown 格式的 TOC"""
        lines = []
        
        for header in headers:
            level = header['level']
            title = header['title']
            
            # 计算缩进
            indent = '  ' * (level - 1)
            
            if include_links:
                # 生成锚点链接
                anchor = self._generate_anchor(title)
                line = f"{indent}- [{title}](#{anchor})"
            else:
                line = f"{indent}- {title}"
            
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _generate_html_toc(self, headers: List[Dict[str, Any]]) -> str:
        """生成 HTML 格式的 TOC"""
        lines = ['<ul>']
        current_level = 0
        
        for header in headers:
            level = header['level']
            title = header['title']
            
            # 处理级别变化
            if level > current_level:
                for _ in range(level - current_level):
                    if current_level > 0:
                        lines.append('  ' * current_level + '<li><ul>')
                    current_level += 1
            elif level < current_level:
                for _ in range(current_level - level):
                    lines.append('  ' * current_level + '</ul></li>')
                    current_level -= 1
            
            # 添加当前项
            indent = '  ' * level
            lines.append(f"{indent}<li>{title}</li>")
        
        # 关闭所有未关闭的标签
        while current_level > 0:
            lines.append('  ' * current_level + '</ul>')
            if current_level > 1:
                lines.append('  ' * (current_level - 1) + '</li>')
            current_level -= 1
        
        return '\n'.join(lines)
    
    def _generate_text_toc(self, headers: List[Dict[str, Any]]) -> str:
        """生成纯文本格式的 TOC"""
        lines = []
        
        for header in headers:
            level = header['level']
            title = header['title']
            line_number = header['line_number']
            
            # 计算缩进
            indent = '  ' * (level - 1)
            line = f"{indent}{title} (第 {line_number} 行)"
            
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _generate_anchor(self, title: str) -> str:
        """为标题生成锚点链接"""
        # 转换为小写
        anchor = title.lower()
        
        # 移除特殊字符，保留中文、英文、数字、连字符
        anchor = re.sub(r'[^\w\u4e00-\u9fff\-]', '-', anchor)
        
        # 移除多余的连字符
        anchor = re.sub(r'-+', '-', anchor)
        anchor = anchor.strip('-')
        
        return anchor


# 便捷函数，供外部直接调用
def extract_toc_from_content(content: str) -> List[Dict[str, Any]]:
    """
    便捷函数：从 Markdown 内容提取 TOC
    
    Args:
        content: Markdown 内容
        
    Returns:
        标题信息列表
    """
    extractor = MarkdownTOCExtractor()
    return extractor.extract_toc(content)


def analyze_numbering_issues_from_headers(headers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    便捷函数：分析标题编号问题
    
    Args:
        headers: 标题信息列表
        
    Returns:
        编号问题分析结果
    """
    extractor = MarkdownTOCExtractor()
    return extractor.analyze_numbering_issues(headers)


def generate_toc_from_headers(headers: List[Dict[str, Any]], 
                              format_type: str = 'markdown',
                              include_links: bool = False,
                              max_level: Optional[int] = None) -> Dict[str, Any]:
    """
    便捷函数：生成 TOC 内容
    
    Args:
        headers: 标题信息列表
        format_type: 输出格式
        include_links: 是否包含链接
        max_level: 最大级别
        
    Returns:
        生成的 TOC 信息
    """
    extractor = MarkdownTOCExtractor()
    return extractor.generate_toc(headers, format_type, include_links, max_level)


if __name__ == "__main__":
    # 简单的测试示例
    test_content = """# 1. 介绍
这是介绍部分。

## 1.1 概述
概述内容。

## 1.2 目标
目标内容。

# 2. 方法
方法部分。

```python
# 这是代码块中的注释
def example():
    pass
```

### 2.1.1 详细步骤
详细步骤。

# 1. 重复标题
这会产生重复编号问题。
"""
    
    print("=== Markdown TOC 核心功能测试 ===")
    
    # 测试 TOC 提取
    extractor = MarkdownTOCExtractor()
    headers = extractor.extract_toc(test_content)
    print(f"\n1. TOC 提取结果 ({len(headers)} 个标题):")
    for header in headers:
        print(f"   L{header['level']}: {header['title']} (第 {header['line_number']} 行)")
    
    # 测试编号问题分析
    issues = extractor.analyze_numbering_issues(headers)
    print(f"\n2. 编号问题分析:")
    print(f"   存在问题: {issues['has_issues']}")
    print(f"   重复编号: {len(issues['duplicate_numbers'])} 个")
    print(f"   不连续编号: {len(issues['discontinuous_numbers'])} 个")
    
    # 测试 TOC 生成
    toc_result = extractor.generate_toc(headers, 'markdown', include_links=True)
    print(f"\n3. TOC 生成结果:")
    print(f"   格式: {toc_result['format']}")
    print(f"   条目数: {toc_result['total_items']}")
    print(f"   内容:\n{toc_result['content']}")