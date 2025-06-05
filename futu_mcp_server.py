#!/usr/bin/env python3
"""
富途 MCP 服务器

本模块将富途API客户端功能暴露为 MCP (Model Context Protocol) 工具，
允许 AI 助手通过标准化接口访问富途的股票数据。

支持的工具:
- get_watchlist: 获取用户的自选股列表
- get_stock_quote: 获取股票实时报价 (待实现)
- get_stock_history: 获取股票历史数据 (待实现)
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import BaseModel, Field

# 导入富途客户端
from trademind.scheduler.futu_client import FutuClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 MCP 服务器实例
server = Server("futu-mcp-server")

# 全局富途客户端实例
futu_client: Optional[FutuClient] = None


class FutuConfig(BaseModel):
    """富途API配置"""
    host: str = Field(default="127.0.0.1", description="富途API主机地址")
    port: int = Field(default=11111, description="富途API端口")
    unlock_pwd: Optional[str] = Field(default=None, description="解锁密码")


def initialize_futu_client(config: Optional[Dict] = None) -> FutuClient:
    """初始化富途客户端"""
    global futu_client
    
    if futu_client is None:
        if config is None:
            # 从环境变量读取配置，如果没有则使用默认值
            config = {
                "host": os.getenv("FUTU_API_HOST", "127.0.0.1"),
                "port": int(os.getenv("FUTU_API_PORT", "11111"))
            }
            
            # 如果设置了解锁密码环境变量
            unlock_pwd = os.getenv("FUTU_UNLOCK_PASSWORD")
            if unlock_pwd:
                config["unlock_pwd"] = unlock_pwd
                
        futu_client = FutuClient(config)
        logger.info(f"富途客户端已初始化: {config['host']}:{config['port']}")
    
    return futu_client


@server.list_tools()
async def list_tools() -> List[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="get_watchlist",
            description="获取富途用户的自选股列表，返回股票代码到股票名称的映射",
            inputSchema={
                "type": "object",
                "properties": {
                    "market": {
                        "type": "string",
                        "description": "市场类型，默认为'美股'",
                        "default": "美股",
                        "enum": ["美股", "港股", "A股"]
                    }
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="configure_futu_client",
            description="配置富途API客户端连接参数",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "富途API主机地址",
                        "default": "127.0.0.1"
                    },
                    "port": {
                        "type": "integer",
                        "description": "富途API端口",
                        "default": 11111
                    },
                    "unlock_pwd": {
                        "type": "string",
                        "description": "解锁密码（可选）"
                    }
                },
                "required": ["host", "port"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_client_status",
            description="获取富途客户端连接状态和配置信息",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    try:
        if name == "get_watchlist":
            return await handle_get_watchlist(arguments)
        elif name == "configure_futu_client":
            return await handle_configure_client(arguments)
        elif name == "get_client_status":
            return await handle_get_client_status(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"未知的工具: {name}"
            )]
    
    except Exception as e:
        logger.error(f"工具调用失败 {name}: {e}")
        return [TextContent(
            type="text",
            text=f"工具调用失败: {str(e)}"
        )]


async def handle_get_watchlist(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理获取自选股列表的请求"""
    market = arguments.get("market", "美股")
    
    try:
        # 确保客户端已初始化
        client = initialize_futu_client()
        
        # 获取自选股列表
        watchlist = client.get_watchlist()
        
        if not watchlist:
            return [TextContent(
                type="text",
                text=f"未获取到{market}自选股数据，可能的原因：\n"
                     f"1. 富途客户端未运行或未登录\n"
                     f"2. API连接配置错误\n"
                     f"3. 自选股列表为空\n"
                     f"4. 网络连接问题"
            )]
        
        # 格式化输出
        result = {
            "market": market,
            "count": len(watchlist),
            "stocks": watchlist,
            "timestamp": str(asyncio.get_event_loop().time())
        }
        
        # 创建友好的文本输出
        text_output = f"📈 {market}自选股列表 ({len(watchlist)}只)\n\n"
        
        if watchlist:
            for code, name in watchlist.items():
                text_output += f"• {code}: {name}\n"
        else:
            text_output += "暂无自选股数据"
        
        text_output += f"\n🔄 数据获取时间: {result['timestamp']}"
        
        return [
            TextContent(
                type="text", 
                text=text_output
            ),
            TextContent(
                type="text",
                text=f"JSON格式数据:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"获取自选股失败: {e}")
        return [TextContent(
            type="text",
            text=f"获取自选股失败: {str(e)}\n\n"
                 f"请确保：\n"
                 f"1. 富途客户端已启动并登录\n"
                 f"2. API接口已开启\n"
                 f"3. 网络连接正常"
        )]


async def handle_configure_client(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理配置客户端的请求"""
    global futu_client
    
    try:
        config = {
            "host": arguments.get("host", "127.0.0.1"),
            "port": arguments.get("port", 11111)
        }
        
        if "unlock_pwd" in arguments:
            config["unlock_pwd"] = arguments["unlock_pwd"]
        
        # 重新初始化客户端
        futu_client = None
        client = initialize_futu_client(config)
        
        return [TextContent(
            type="text",
            text=f"✅ 富途客户端配置已更新:\n"
                 f"• 主机: {config['host']}\n"
                 f"• 端口: {config['port']}\n"
                 f"• 解锁密码: {'已设置' if config.get('unlock_pwd') else '未设置'}"
        )]
        
    except Exception as e:
        logger.error(f"配置客户端失败: {e}")
        return [TextContent(
            type="text",
            text=f"配置客户端失败: {str(e)}"
        )]


async def handle_get_client_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理获取客户端状态的请求"""
    global futu_client
    
    try:
        if futu_client is None:
            return [TextContent(
                type="text",
                text="❌ 富途客户端未初始化\n\n"
                     "请先使用 configure_futu_client 工具配置客户端"
            )]
        
        status_info = {
            "initialized": futu_client is not None,
            "host": getattr(futu_client, 'host', 'unknown'),
            "port": getattr(futu_client, 'port', 'unknown'),
            "last_error": getattr(futu_client, 'last_error', None)
        }
        
        status_text = f"🔗 富途客户端状态:\n\n"
        status_text += f"• 状态: {'✅ 已初始化' if status_info['initialized'] else '❌ 未初始化'}\n"
        status_text += f"• 主机: {status_info['host']}\n"
        status_text += f"• 端口: {status_info['port']}\n"
        
        if status_info['last_error']:
            status_text += f"• 最后错误: {status_info['last_error']}\n"
        else:
            status_text += f"• 最后错误: 无\n"
        
        return [
            TextContent(type="text", text=status_text),
            TextContent(
                type="text",
                text=f"JSON格式状态:\n```json\n{json.dumps(status_info, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"获取客户端状态失败: {e}")
        return [TextContent(
            type="text",
            text=f"获取客户端状态失败: {str(e)}"
        )]


async def main():
    """启动 MCP 服务器"""
    logger.info("启动富途 MCP 服务器...")
    
    # 初始化默认客户端
    try:
        initialize_futu_client()
        logger.info("富途客户端初始化成功")
    except Exception as e:
        logger.warning(f"富途客户端初始化失败: {e}")
        logger.info("服务器将继续运行，可稍后通过工具配置客户端")
    
    # 启动服务器
    async with server.run_stdio() as streams:
        await server.run(
            streams[0], streams[1],
            initialization_options={
                "server_name": "futu-mcp-server",
                "server_version": "1.0.0",
                "capabilities": {
                    "tools": {}
                }
            }
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        sys.exit(1) 