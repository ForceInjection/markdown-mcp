#!/bin/bash
# -*- coding: utf-8 -*-

# TRAE MCP Server 停止脚本
# 用于优雅地停止 MCP 服务器进程

set -e

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

log_info "TRAE MCP Server 停止脚本开始执行..."

# 查找 MCP 服务器进程
MCP_PIDS=$(pgrep -f "mcp_server.py" 2>/dev/null || true)

if [ -z "$MCP_PIDS" ]; then
    log_warning "未找到运行中的 MCP 服务器进程"
    exit 0
fi

log_info "找到 MCP 服务器进程: $MCP_PIDS"

# 优雅停止进程
for PID in $MCP_PIDS; do
    log_info "正在停止进程 $PID..."
    
    # 首先发送 SIGTERM 信号
    if kill -TERM "$PID" 2>/dev/null; then
        log_info "已发送 SIGTERM 信号到进程 $PID"
        
        # 等待进程优雅退出
        WAIT_COUNT=0
        while [ $WAIT_COUNT -lt 10 ]; do
            if ! kill -0 "$PID" 2>/dev/null; then
                log_success "进程 $PID 已优雅退出"
                break
            fi
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done
        
        # 如果进程仍在运行，强制终止
        if kill -0 "$PID" 2>/dev/null; then
            log_warning "进程 $PID 未在规定时间内退出，强制终止..."
            if kill -KILL "$PID" 2>/dev/null; then
                log_success "进程 $PID 已强制终止"
            else
                log_error "无法终止进程 $PID"
            fi
        fi
    else
        log_error "无法发送信号到进程 $PID"
    fi
done

log_success "MCP 服务器停止脚本执行完成"