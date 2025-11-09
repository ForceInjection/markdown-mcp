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

# 或者使用 setup.py 安装
./venv/bin/pip install -e .
```

## 2. 启动服务器

### 方式一：使用启动脚本（推荐用于 TRAE）

```bash
# 启动 TOC 服务器
./start_mcp_for_trae.sh

# 或者启动编辑器服务器
./start_mcp_for_trae.sh --editor
```

### 方式二：使用包安装后的命令

```bash
# 启动 Markdown TOC MCP Server
markdown-toc-mcp-server

# 启动 Markdown Editor MCP Server
markdown-editor-mcp-server

# 或者使用快捷启动命令
start-markdown-toc-server
start-markdown-editor-server
```

### 方式三：手动启动

```bash
source venv/bin/activate

# 启动 TOC 服务器
python src/server/toc_mcp_server.py

# 启动编辑器服务器
python src/server/editor_mcp_server.py
```

---

## 3. 配置文件说明

项目配置文件位于：`config/` 目录

### 3.1 TOC 服务器配置文件 (`config/toc_mcp_config.json`)

此文件包含 TOC 服务器的默认配置模板。

### 3.2 编辑器服务器配置文件 (`config/editor_mcp_config.json`)

此文件包含编辑器服务器的默认配置模板。

> **注意**：这些是配置模板文件，实际使用时需要根据部署环境调整路径参数。

---

## 4. 日志配置

- TOC 服务器日志：`logs/toc_mcp_server.log`
- 编辑器服务器日志：`logs/editor_mcp_server.log`
- 日志轮转：最大 10MB，保留 5 个备份文件
- 日志级别：INFO（控制台）、DEBUG（文件）

---

## 5. 安装和配置故障排除

### 5.1 依赖安装问题

**ModuleNotFoundError: No module named 'mcp'**
确保使用虚拟环境中的 Python 解释器：

```bash
./venv/bin/python src/server/toc_mcp_server.py
./venv/bin/python src/server/editor_mcp_server.py
```

### 5.2 权限问题

确保启动脚本有执行权限：

```bash
chmod +x start_mcp_for_trae.sh
chmod +x stop_mcp_for_trae.sh
```

### 5.3 日志文件不生成

检查 `logs/` 目录权限，确保应用有写入权限：

```bash
mkdir -p logs
chmod 755 logs
```

### 5.4 端口冲突

如果遇到端口冲突，可以修改服务器启动端口：

```bash
# 指定端口启动
python src/server/toc_mcp_server.py --port 8081
python src/server/editor_mcp_server.py --port 8082
```

### 5.5 配置文件路径问题

确保配置文件中的路径指向正确的启动脚本位置。
