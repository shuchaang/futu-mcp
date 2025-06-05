"""
富途 MCP 服务器包

本包将富途API客户端功能暴露为 MCP (Model Context Protocol) 工具，
允许 AI 助手通过标准化接口访问富途的股票数据。

主要模块:
- futu_mcp_server: MCP 服务器主程序
- start_futu_mcp: 启动脚本

使用方法:
    from futu_mcp import start_futu_mcp
    # 或者
    python -m futu_mcp.start_futu_mcp
"""

__version__ = "1.0.0"
__author__ = "TradeMind Team"
__description__ = "富途API MCP服务器 - 提供富途股票数据访问功能"

# 导出主要组件
from .futu_mcp_server import server, initialize_futu_client

__all__ = [
    "server",
    "initialize_futu_client",
    "__version__",
    "__author__",
    "__description__"
] 