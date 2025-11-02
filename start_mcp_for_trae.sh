#!/bin/bash
# -*- coding: utf-8 -*-

# TRAE MCP Server 启动脚本
# 专门用于在 TRAE IDE 中配置 MCP 服务器
# 
# 功能：
# 1. 自动检查和创建虚拟环境
# 2. 自动安装项目依赖
# 3. 启动 MCP 服务器
# 4. 提供详细的日志和错误处理

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
MCP_SERVER_SCRIPT="$SCRIPT_DIR/src/server/mcp_server.py"

log_info "TRAE MCP Server 启动脚本开始执行..."
log_info "项目目录: $SCRIPT_DIR"

# 切换到项目目录
cd "$SCRIPT_DIR"

# 检查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    log_error "Python3 未找到，请先安装 Python 3.8 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
log_info "检测到 Python 版本: $PYTHON_VERSION"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_DIR" ]; then
    log_warning "虚拟环境不存在，正在创建..."
    
    # 创建虚拟环境
    if python3 -m venv "$VENV_DIR"; then
        log_success "虚拟环境创建成功: $VENV_DIR"
    else
        log_error "虚拟环境创建失败"
        exit 1
    fi
else
    log_info "虚拟环境已存在: $VENV_DIR"
fi

# 检查虚拟环境的 Python 解释器
VENV_PYTHON="$VENV_DIR/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    log_error "虚拟环境中的 Python 解释器不存在: $VENV_PYTHON"
    exit 1
fi

# 检查 requirements.txt 是否存在
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    log_error "依赖文件不存在: $REQUIREMENTS_FILE"
    exit 1
fi

# 检查是否需要安装依赖
log_info "检查项目依赖..."
if ! "$VENV_PYTHON" -c "import mcp" &> /dev/null; then
    log_warning "MCP 依赖未安装，正在安装项目依赖..."
    
    # 升级 pip
    log_info "升级 pip..."
    "$VENV_PYTHON" -m pip install --upgrade pip
    
    # 安装依赖
    log_info "安装项目依赖..."
    if "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE"; then
        log_success "依赖安装成功"
    else
        log_error "依赖安装失败"
        exit 1
    fi
else
    log_info "项目依赖已安装"
fi

# 检查 MCP 服务器脚本是否存在
if [ ! -f "$MCP_SERVER_SCRIPT" ]; then
    log_error "MCP 服务器脚本不存在: $MCP_SERVER_SCRIPT"
    exit 1
fi

# 创建日志目录
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# 设置信号处理，优雅关闭
cleanup() {
    log_info "接收到停止信号，正在关闭 MCP 服务器..."
    if [ ! -z "$MCP_PID" ]; then
        kill -TERM "$MCP_PID" 2>/dev/null || true
        wait "$MCP_PID" 2>/dev/null || true
    fi
    log_success "MCP 服务器已停止"
    exit 0
}

trap cleanup SIGTERM SIGINT

log_success "环境检查完成，启动 MCP 服务器..."
log_info "服务器脚本: $MCP_SERVER_SCRIPT"
log_info "日志目录: $LOG_DIR"
log_info "使用 Ctrl+C 停止服务器"

# 启动 MCP 服务器
exec "$VENV_PYTHON" "$MCP_SERVER_SCRIPT"