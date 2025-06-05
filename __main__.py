#!/usr/bin/env python3
"""
富途 MCP 服务器包主入口

支持通过以下方式运行:
    python -m futu_mcp
    python -m futu_mcp --help
    python -m futu_mcp --host 127.0.0.1 --port 11111
"""

import sys
from pathlib import Path

# 添加父目录到路径，确保可以导入 trademind 模块
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

if __name__ == "__main__":
    from .start_futu_mcp import main
    main() 