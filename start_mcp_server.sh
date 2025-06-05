#!/bin/bash

# 富途 MCP 服务器启动脚本
# 确保使用虚拟环境中的Python

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 激活虚拟环境
source "$SCRIPT_DIR/venv/bin/activate"

# 设置环境变量
export PYTHONPATH="$SCRIPT_DIR"

# 启动MCP服务器
python "$SCRIPT_DIR/futu_mcp_server.py" "$@" 