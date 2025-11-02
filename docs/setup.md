# MCP 服务器设置说明

## 1. 依赖安装

项目已配置虚拟环境，所有依赖已安装在 `venv/` 目录中。

如需重新安装依赖：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
./venv/bin/pip install -r requirements.txt
```

## 2. 启动服务器

### 方式一：直接启动（推荐用于 TRAE）

```bash
./start_mcp_for_trae.sh
```

### 方式二：使用完整启动脚本

```bash
./scripts/start_mcp_server.sh
```

### 方式三：手动启动

```bash
source venv/bin/activate
python src/server/mcp_server.py
```

## 3. TRAE 配置

TRAE 配置文件位于：`config/trae_mcp_config.json`

配置已更新为使用启动脚本：

```json
{
  "mcpServers": {
    "markdown-toc": {
      "command": "/Users/wangtianqing/Project/mcp/mcp/start_mcp_for_trae.sh",
      "args": []
    }
  }
}
```

## 4. 日志文件

- 日志文件位置：`logs/mcp_server.log`
- 日志轮转：最大 10MB，保留 5 个备份文件
- 日志级别：INFO（控制台）、DEBUG（文件）

## 5. 故障排除

### 5.1 ModuleNotFoundError: No module named 'mcp'

确保使用虚拟环境中的 Python 解释器：

```bash
./venv/bin/python src/server/mcp_server.py
```

### 5.2 权限问题

确保启动脚本有执行权限：

```bash
chmod +x start_mcp_for_trae.sh
chmod +x scripts/start_mcp_server.sh
```

### 5.3 日志文件不生成

检查 `logs/` 目录权限，确保应用有写入权限。
