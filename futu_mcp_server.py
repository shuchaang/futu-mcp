#!/usr/bin/env python3
"""
富途 MCP 服务器

本模块将富途API客户端功能暴露为 MCP (Model Context Protocol) 工具，
允许 AI 助手通过标准化接口访问富途的股票数据和交易功能。

支持的工具:
- get_watchlist: 获取用户的自选股列表
- get_stock_quote: 获取股票实时报价信息
- get_stock_history: 获取股票历史K线数据
- search_stock: 搜索股票，根据名称或代码查找
- get_market_snapshot: 获取市场快照和主要指数
- get_account_info: 获取账户信息（需要交易权限）
- get_positions: 获取持仓信息（需要交易权限）
- configure_futu_client: 配置富途API客户端连接
- get_client_status: 获取客户端连接状态

基于富途OpenAPI文档: https://openapi.futunn.com/futu-api-doc/
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
            name="get_stock_quote",
            description="获取股票实时报价信息，包括最新价、涨跌幅、成交量等",
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "股票代码，如 'AAPL', 'HK.00700', 'SZ.000001'"
                    },
                    "market": {
                        "type": "string",
                        "description": "市场类型",
                        "enum": ["US", "HK", "SH", "SZ"],
                        "default": "US"
                    }
                },
                "required": ["stock_code"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_stock_history",
            description="获取股票历史K线数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "股票代码，如 'AAPL', 'HK.00700', 'SZ.000001'"
                    },
                    "period": {
                        "type": "string",
                        "description": "K线周期",
                        "enum": ["1min", "5min", "15min", "30min", "60min", "day", "week", "month"],
                        "default": "day"
                    },
                    "count": {
                        "type": "integer",
                        "description": "获取数据条数，默认30条",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["stock_code"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="search_stock",
            description="搜索股票，根据股票名称或代码查找相关股票",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，可以是股票名称或代码"
                    },
                    "market": {
                        "type": "string",
                        "description": "搜索市场",
                        "enum": ["US", "HK", "SH", "SZ", "ALL"],
                        "default": "ALL"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["keyword"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_market_snapshot",
            description="获取市场快照，包括主要指数和热门股票",
            inputSchema={
                "type": "object",
                "properties": {
                    "market": {
                        "type": "string",
                        "description": "市场类型",
                        "enum": ["US", "HK", "CN"],
                        "default": "US"
                    }
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_account_info",
            description="获取账户信息，包括资产、持仓等（需要交易权限）",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "description": "账户类型",
                        "enum": ["REAL", "SIMULATE"],
                        "default": "SIMULATE"
                    }
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_positions",
            description="获取持仓信息（需要交易权限）",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "description": "账户类型",
                        "enum": ["REAL", "SIMULATE"],
                        "default": "SIMULATE"
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
        elif name == "get_stock_quote":
            return await handle_get_stock_quote(arguments)
        elif name == "get_stock_history":
            return await handle_get_stock_history(arguments)
        elif name == "search_stock":
            return await handle_search_stock(arguments)
        elif name == "get_market_snapshot":
            return await handle_get_market_snapshot(arguments)
        elif name == "get_account_info":
            return await handle_get_account_info(arguments)
        elif name == "get_positions":
            return await handle_get_positions(arguments)
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


async def handle_get_stock_quote(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理获取股票实时报价的请求"""
    stock_code = arguments.get("stock_code")
    market = arguments.get("market", "US")
    
    try:
        # 确保客户端已初始化
        client = initialize_futu_client()
        
        # 格式化股票代码
        if market and not stock_code.startswith(market + "."):
            formatted_code = f"{market}.{stock_code}"
        else:
            formatted_code = stock_code
        
        # 获取股票报价（这里需要根据实际的FutuClient API调整）
        # 假设FutuClient有get_stock_quote方法
        if hasattr(client, 'get_stock_quote'):
            quote_data = client.get_stock_quote(formatted_code)
        else:
            # 如果没有该方法，返回提示信息
            return [TextContent(
                type="text",
                text=f"⚠️ 股票报价功能暂未实现\n\n"
                     f"请求的股票: {formatted_code}\n"
                     f"该功能需要在FutuClient中实现get_stock_quote方法"
            )]
        
        if not quote_data:
            return [TextContent(
                type="text",
                text=f"❌ 未能获取股票 {formatted_code} 的报价数据\n\n"
                     f"可能的原因：\n"
                     f"1. 股票代码不正确\n"
                     f"2. 市场未开盘\n"
                     f"3. 网络连接问题\n"
                     f"4. API权限不足"
            )]
        
        # 格式化输出
        text_output = f"📊 {formatted_code} 实时报价\n\n"
        
        if isinstance(quote_data, dict):
            for key, value in quote_data.items():
                text_output += f"• {key}: {value}\n"
        else:
            text_output += f"数据: {quote_data}\n"
        
        return [
            TextContent(type="text", text=text_output),
            TextContent(
                type="text",
                text=f"JSON格式数据:\n```json\n{json.dumps(quote_data, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"获取股票报价失败: {e}")
        return [TextContent(
            type="text",
            text=f"获取股票报价失败: {str(e)}"
        )]


async def handle_get_stock_history(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理获取股票历史数据的请求"""
    stock_code = arguments.get("stock_code")
    period = arguments.get("period", "day")
    count = arguments.get("count", 30)
    
    try:
        # 确保客户端已初始化
        client = initialize_futu_client()
        
        # 获取历史数据（这里需要根据实际的FutuClient API调整）
        if hasattr(client, 'get_stock_history'):
            history_data = client.get_stock_history(stock_code, period, count)
        else:
            return [TextContent(
                type="text",
                text=f"⚠️ 股票历史数据功能暂未实现\n\n"
                     f"请求参数:\n"
                     f"• 股票代码: {stock_code}\n"
                     f"• 周期: {period}\n"
                     f"• 数量: {count}\n\n"
                     f"该功能需要在FutuClient中实现get_stock_history方法"
            )]
        
        if not history_data:
            return [TextContent(
                type="text",
                text=f"❌ 未能获取股票 {stock_code} 的历史数据"
            )]
        
        # 格式化输出
        text_output = f"📈 {stock_code} 历史数据 ({period}, {count}条)\n\n"
        
        if isinstance(history_data, list) and len(history_data) > 0:
            # 显示最近几条数据
            recent_count = min(5, len(history_data))
            text_output += f"最近{recent_count}条数据:\n"
            for i, data in enumerate(history_data[-recent_count:]):
                text_output += f"{i+1}. {data}\n"
        else:
            text_output += f"数据: {history_data}\n"
        
        return [
            TextContent(type="text", text=text_output),
            TextContent(
                type="text",
                text=f"完整JSON数据:\n```json\n{json.dumps(history_data, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"获取股票历史数据失败: {e}")
        return [TextContent(
            type="text",
            text=f"获取股票历史数据失败: {str(e)}"
        )]


async def handle_search_stock(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理搜索股票的请求"""
    keyword = arguments.get("keyword")
    market = arguments.get("market", "ALL")
    limit = arguments.get("limit", 10)
    
    try:
        # 确保客户端已初始化
        client = initialize_futu_client()
        
        # 搜索股票
        if hasattr(client, 'search_stock'):
            search_results = client.search_stock(keyword, market, limit)
        else:
            return [TextContent(
                type="text",
                text=f"⚠️ 股票搜索功能暂未实现\n\n"
                     f"搜索参数:\n"
                     f"• 关键词: {keyword}\n"
                     f"• 市场: {market}\n"
                     f"• 限制: {limit}\n\n"
                     f"该功能需要在FutuClient中实现search_stock方法"
            )]
        
        if not search_results:
            return [TextContent(
                type="text",
                text=f"🔍 未找到与 '{keyword}' 相关的股票"
            )]
        
        # 格式化输出
        text_output = f"🔍 搜索结果: '{keyword}' (市场: {market})\n\n"
        
        if isinstance(search_results, list):
            for i, stock in enumerate(search_results[:limit], 1):
                text_output += f"{i}. {stock}\n"
        else:
            text_output += f"结果: {search_results}\n"
        
        return [
            TextContent(type="text", text=text_output),
            TextContent(
                type="text",
                text=f"JSON格式结果:\n```json\n{json.dumps(search_results, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        return [TextContent(
            type="text",
            text=f"搜索股票失败: {str(e)}"
        )]


async def handle_get_market_snapshot(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理获取市场快照的请求"""
    market = arguments.get("market", "US")
    
    try:
        # 确保客户端已初始化
        client = initialize_futu_client()
        
        # 获取市场快照
        if hasattr(client, 'get_market_snapshot'):
            snapshot_data = client.get_market_snapshot(market)
        else:
            return [TextContent(
                type="text",
                text=f"⚠️ 市场快照功能暂未实现\n\n"
                     f"请求市场: {market}\n\n"
                     f"该功能需要在FutuClient中实现get_market_snapshot方法"
            )]
        
        if not snapshot_data:
            return [TextContent(
                type="text",
                text=f"❌ 未能获取 {market} 市场快照数据"
            )]
        
        # 格式化输出
        text_output = f"📊 {market} 市场快照\n\n"
        
        if isinstance(snapshot_data, dict):
            for key, value in snapshot_data.items():
                text_output += f"• {key}: {value}\n"
        else:
            text_output += f"数据: {snapshot_data}\n"
        
        return [
            TextContent(type="text", text=text_output),
            TextContent(
                type="text",
                text=f"JSON格式数据:\n```json\n{json.dumps(snapshot_data, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"获取市场快照失败: {e}")
        return [TextContent(
            type="text",
            text=f"获取市场快照失败: {str(e)}"
        )]


async def handle_get_account_info(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理获取账户信息的请求"""
    account_type = arguments.get("account_type", "SIMULATE")
    
    try:
        # 确保客户端已初始化
        client = initialize_futu_client()
        
        # 获取账户信息
        if hasattr(client, 'get_account_info'):
            account_data = client.get_account_info(account_type)
        else:
            return [TextContent(
                type="text",
                text=f"⚠️ 账户信息功能暂未实现\n\n"
                     f"账户类型: {account_type}\n\n"
                     f"该功能需要在FutuClient中实现get_account_info方法\n"
                     f"注意：此功能需要交易权限"
            )]
        
        if not account_data:
            return [TextContent(
                type="text",
                text=f"❌ 未能获取 {account_type} 账户信息\n\n"
                     f"可能的原因：\n"
                     f"1. 账户未登录\n"
                     f"2. 没有交易权限\n"
                     f"3. 账户类型错误"
            )]
        
        # 格式化输出
        text_output = f"💰 {account_type} 账户信息\n\n"
        
        if isinstance(account_data, dict):
            for key, value in account_data.items():
                text_output += f"• {key}: {value}\n"
        else:
            text_output += f"数据: {account_data}\n"
        
        return [
            TextContent(type="text", text=text_output),
            TextContent(
                type="text",
                text=f"JSON格式数据:\n```json\n{json.dumps(account_data, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"获取账户信息失败: {e}")
        return [TextContent(
            type="text",
            text=f"获取账户信息失败: {str(e)}"
        )]


async def handle_get_positions(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理获取持仓信息的请求"""
    account_type = arguments.get("account_type", "SIMULATE")
    
    try:
        # 确保客户端已初始化
        client = initialize_futu_client()
        
        # 获取持仓信息
        if hasattr(client, 'get_positions'):
            positions_data = client.get_positions(account_type)
        else:
            return [TextContent(
                type="text",
                text=f"⚠️ 持仓信息功能暂未实现\n\n"
                     f"账户类型: {account_type}\n\n"
                     f"该功能需要在FutuClient中实现get_positions方法\n"
                     f"注意：此功能需要交易权限"
            )]
        
        if not positions_data:
            return [TextContent(
                type="text",
                text=f"📊 {account_type} 账户暂无持仓\n\n"
                     f"或者未能获取持仓数据"
            )]
        
        # 格式化输出
        text_output = f"📊 {account_type} 持仓信息\n\n"
        
        if isinstance(positions_data, list):
            for i, position in enumerate(positions_data, 1):
                text_output += f"{i}. {position}\n"
        elif isinstance(positions_data, dict):
            for key, value in positions_data.items():
                text_output += f"• {key}: {value}\n"
        else:
            text_output += f"数据: {positions_data}\n"
        
        return [
            TextContent(type="text", text=text_output),
            TextContent(
                type="text",
                text=f"JSON格式数据:\n```json\n{json.dumps(positions_data, ensure_ascii=False, indent=2)}\n```"
            )
        ]
        
    except Exception as e:
        logger.error(f"获取持仓信息失败: {e}")
        return [TextContent(
            type="text",
            text=f"获取持仓信息失败: {str(e)}"
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
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            initialization_options={
                "server_name": "futu-mcp-server",
                "server_version": "1.1.0",
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