# -*- coding: utf-8 -*-
"""
Markdown TOC 核心功能模块

提供 Markdown 文档的目录提取、编号分析和结构分析功能。
"""

# 语义编辑器功能
from .semantic_editor import SemanticEditor, create_editor_from_markdown, EditOperation, EditResult

__all__ = ['SemanticEditor', 'create_editor_from_markdown', 'EditOperation', 'EditResult']