#!/usr/bin/env python3
"""
富途MCP服务器 - 修复版本

基于simple_futu_real.py的稳定架构，但包含所有新功能。
确保工具能正确注册和识别。
"""

import asyncio
import sys
import os
from pathlib import Path
import pandas as pd

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions

# 富途客户端
futu_client = None

def init_futu_client():
    """初始化富途客户端"""
    global futu_client
    
    try:
        from trademind.scheduler.futu_client import FutuClient
        
        # 从环境变量获取配置
        host = os.getenv("FUTU_HOST", "127.0.0.1")
        port = int(os.getenv("FUTU_PORT", "11111"))
        unlock_pwd = os.getenv("FUTU_UNLOCK_PWD", "")
        
        print(f"🔗 连接富途API: {host}:{port}", file=sys.stderr)
        
        config = {
            "host": host,
            "port": port,
            "unlock_pwd": unlock_pwd if unlock_pwd else None
        }
        
        futu_client = FutuClient(config)
        
        if futu_client.quote_ctx:
            print("✅ 富途行情API连接成功", file=sys.stderr)
        else:
            print("❌ 富途行情API连接失败", file=sys.stderr)
            return False
            
        if unlock_pwd and futu_client.trade_ctx:
            print("✅ 富途交易API连接成功", file=sys.stderr)
        elif unlock_pwd:
            print("❌ 富途交易API连接失败", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"❌ 富途客户端初始化失败: {e}", file=sys.stderr)
        futu_client = None
        return False

# 创建服务器
server = Server("futu-mcp-enhanced")

@server.list_tools()
async def list_tools():
    """列出所有工具"""
    return [  
        Tool(
            name="get_user_security",
            description="获取自选股列表，查看指定分组的自选股票",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_name": {
                        "type": "string",
                        "description": "自选股分组名称。系统分组：全部、沪深、港股、美股、期权、港股期权、美股期权、特别关注、期货",
                        "default": "全部"
                    }
                },
                "required": ["group_name"],
                "additionalProperties": False
            }
        ),
        
        Tool(
            name="get_user_security_group",
            description="获取自选股分组列表，查看所有可用的自选股分组",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_type": {
                        "type": "string",
                        "description": "分组类型筛选",
                        "enum": ["ALL", "SYSTEM", "CUSTOM"],
                        "default": "ALL"
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
                        "enum": ["REAL", ],
                        "default": "REAL"
                    }
                },
                "additionalProperties": False
            }
        ),

        Tool(
            name="get_market_snapshot",
            description="获取股票快照数据，包含实时价格、交易量、市值等详细信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "code_list": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "股票代码列表，如 ['US.AAPL', 'HK.00700']。每次最多可请求400个标的",
                        "maxItems": 400
                    }
                },
                "required": ["code_list"],
                "additionalProperties": False
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """处理工具调用"""
    print(f"🔧 调用工具: {name}, 参数: {arguments}", file=sys.stderr)
    
    if not futu_client:
        return [TextContent(
            type="text",
            text="❌ 富途客户端未连接\n\n请确保:\n1. 富途牛牛客户端已启动并登录\n2. API接口已开启\n3. 网络连接正常"
        )]
    
    try:
        # 我的自选股
        if name == "get_user_security":
            group_name = arguments.get("group_name", "特别关注")
            
            # 调用富途客户端获取自选股列表
            user_securities = futu_client.get_user_security(group_name)
            
            if not user_securities:
                return [TextContent(
                    type="text",
                    text=f"❌ 未能获取自选股分组 '{group_name}' 的数据\n\n可能原因:\n1. 分组名称不存在\n2. 分组为空\n3. 网络连接问题"
                )]
            
            # 格式化输出
            text_output = f"⭐ 自选股列表 - {group_name}\n"
            text_output += "=" * 60 + "\n\n"
            text_output += f"📊 共 {len(user_securities)} 只股票\n\n"
            
            # 按市场分组显示
            markets = {}
            for stock in user_securities:
                market = stock.get('市场', 'Unknown')
                if market not in markets:
                    markets[market] = []
                markets[market].append(stock)
            
            market_names = {
                'US': '🇺🇸 美股',
                'HK': '🇭🇰 港股', 
                'SH': '🇨🇳 沪股',
                'SZ': '🇨🇳 深股',
                'Unknown': '❓ 其他'
            }
            
            for market, stocks in markets.items():
                if not stocks:
                    continue
                    
                market_display = market_names.get(market, f'📊 {market}')
                text_output += f"{market_display} ({len(stocks)}只)\n"
                text_output += "-" * 40 + "\n"
                
                for i, stock in enumerate(stocks, 1):
                    code = stock.get('股票代码', '')
                    name = stock.get('股票名称', '')
                    stock_type = stock.get('股票类型', '')
                    
                    # 根据股票类型选择emoji
                    if stock_type == 'STOCK':
                        emoji = '📈'
                    elif stock_type == 'OPTION':
                        emoji = '🎯'
                    elif stock_type == 'FUTURE':
                        emoji = '📊'
                    elif stock_type == 'INDEX':
                        emoji = '📍'
                    else:
                        emoji = '💼'
                    
                    text_output += f"{emoji} {code} - {name}\n"
                    
                    # 如果有额外信息，显示一些关键字段
                    lot_size = stock.get('每手股数')
                    if lot_size:
                        text_output += f"     💼 每手: {lot_size}股\n"
                    
                    listing_date = stock.get('上市时间')
                    if listing_date:
                        text_output += f"     📅 上市: {listing_date}\n"
                
                text_output += "\n"
            
            # 添加使用提示
            text_output += "💡 提示:\n"
            text_output += "• 可以使用 get_stock_quote 获取具体股票的实时报价\n"
            text_output += "• 可以使用 get_stock_history 查看历史走势\n"
            text_output += "• 支持的分组: All, US, HK, CN, Options, Futures, Starred 等"
            
            return [TextContent(type="text", text=text_output)]
        
        elif name == "get_user_security_group":
            group_type = arguments.get("group_type", "ALL")
            
            # 调用富途客户端获取自选股分组列表
            security_groups = futu_client.get_user_security_group(group_type)
            
            if not security_groups:
                return [TextContent(
                    type="text",
                    text=f"❌ 未能获取自选股分组数据\n\n可能原因:\n1. 网络连接问题\n2. 富途客户端未连接\n3. API权限问题"
                )]
            
            # 格式化输出
            text_output = f"📂 自选股分组列表\n"
            text_output += "=" * 50 + "\n\n"
            text_output += f"🔍 筛选类型: {group_type}\n"
            text_output += f"📊 共 {len(security_groups)} 个分组\n\n"
            
            # 按分组类型分类显示
            system_groups = [g for g in security_groups if g.get('分组类型') == 'SYSTEM']
            custom_groups = [g for g in security_groups if g.get('分组类型') == 'CUSTOM']
            
            if system_groups:
                text_output += "🏢 系统分组:\n"
                text_output += "-" * 30 + "\n"
                for i, group in enumerate(system_groups, 1):
                    group_name = group.get('分组名称', '')
                    # 根据分组名称添加合适的emoji
                    if '美股' in group_name or 'US' in group_name:
                        emoji = '🇺🇸'
                    elif '港股' in group_name or 'HK' in group_name:
                        emoji = '🇭🇰'
                    elif '沪深' in group_name or 'CN' in group_name or 'A股' in group_name:
                        emoji = '🇨🇳'
                    elif '期权' in group_name or 'Option' in group_name:
                        emoji = '🎯'
                    elif '期货' in group_name or 'Future' in group_name:
                        emoji = '📊'
                    elif '特别关注' in group_name or 'Starred' in group_name:
                        emoji = '⭐'
                    elif '全部' in group_name or 'All' in group_name:
                        emoji = '📋'
                    else:
                        emoji = '📁'
                    
                    text_output += f"{emoji} {group_name}\n"
                text_output += "\n"
            
            if custom_groups:
                text_output += "🎨 自定义分组:\n"
                text_output += "-" * 30 + "\n"
                for i, group in enumerate(custom_groups, 1):
                    group_name = group.get('分组名称', '')
                    text_output += f"📁 {group_name}\n"
                text_output += "\n"
            
            if not system_groups and not custom_groups:
                text_output += "📭 暂无分组数据\n\n"
            
            # 添加使用提示
            text_output += "💡 使用提示:\n"
            text_output += "• 可以使用 get_user_security 查看具体分组的股票列表\n"
            text_output += "• 系统分组包括：全部、美股、港股、沪深、期权、期货等\n"
            text_output += "• 自定义分组是用户在富途客户端中创建的分组\n"
            text_output += f"• 接口限制：30秒内最多请求10次"
            
            return [TextContent(type="text", text=text_output)]
        
        elif name == "get_positions":
            account_type = arguments.get("account_type", "REAL")
            
            positions = futu_client.get_positions(account_type)
            
            if not positions:
                return [TextContent(
                    type="text",
                    text=f"📊 {account_type} 账户暂无持仓\n\n可能需要设置解锁密码"
                )]
            
            text_output = f"📊 {account_type} 持仓信息\n"
            text_output += "=" * 50 + "\n\n"
            text_output += f"持仓总数: {len(positions)}\n\n"
            
            total_pl = 0
            for i, position in enumerate(positions, 1):
                code = position.get('股票代码', f'股票{i}')
                name = position.get('股票名称', '')
                qty = position.get('持仓数量', 0)
                cost = position.get('成本价', 0)
                current = position.get('当前价', 0)
                pl = position.get('盈亏', 0)
                pl_ratio = position.get('盈亏比例', '0%')
                
                emoji = "📈" if pl > 0 else "📉" if pl < 0 else "➡️"
                
                text_output += f"{i}. {code} - {name}\n"
                text_output += f"   📊 持仓: {qty:,.0f} 股\n"
                text_output += f"   💰 成本: ${cost:.2f} | 现价: ${current:.2f}\n"
                text_output += f"   {emoji} 盈亏: ${pl:+,.2f} ({pl_ratio})\n\n"
                
                total_pl += pl
            
            text_output += f"💰 总盈亏: ${total_pl:+,.2f}"
            
            return [TextContent(type="text", text=text_output)]
        
        elif name == "get_market_snapshot":
            code_list = arguments.get("code_list", [])
            
            if not code_list:
                return [TextContent(
                    type="text",
                    text="❌ 请提供股票代码列表"
                )]
            
            # 调用富途客户端获取快照数据
            snapshot_data = futu_client.get_market_snapshot(code_list)
            
            if not snapshot_data or "error" in snapshot_data:
                return [TextContent(
                    type="text",
                    text=f"❌ 获取快照数据失败: {snapshot_data.get('error', '未知错误')}"
                )]
            
            # 格式化输出
            text_output = "📊 市场快照\n"
            text_output += "=" * 60 + "\n\n"
            
            snapshots = snapshot_data.get("快照数据", [])
            text_output += f"共 {len(snapshots)} 个股票的快照数据\n\n"
            
            for snapshot in snapshots:
                code = snapshot.get("股票代码", "")
                name = snapshot.get("股票名称", "")
                price = snapshot.get("最新价", 0)
                change = float(snapshot.get("最新价", 0)) - float(snapshot.get("昨收价", 0))
                change_ratio = (change / float(snapshot.get("昨收价", 1))) * 100
                volume = snapshot.get("成交量", 0)
                turnover = snapshot.get("成交额", 0)
                
                # 根据涨跌选择emoji
                if change > 0:
                    emoji = "📈"
                elif change < 0:
                    emoji = "📉"
                else:
                    emoji = "📊"
                
                text_output += f"{emoji} {code} - {name}\n"
                text_output += f"   最新价: {price:.3f} | 涨跌: {change:+.3f} ({change_ratio:+.2f}%)\n"
                text_output += f"   成交量: {volume:,} | 成交额: {turnover:,.2f}\n"
                
                # 添加其他重要指标
                if snapshot.get("市盈率"):
                    text_output += f"   市盈率: {snapshot.get('市盈率', 0):.2f}"
                if snapshot.get("市净率"):
                    text_output += f" | 市净率: {snapshot.get('市净率', 0):.2f}"
                if snapshot.get("股息率(TTM)"):
                    text_output += f" | 股息率: {snapshot.get('股息率(TTM)', '0.00%')}"
                text_output += "\n"
                
                # 添加52周价格区间
                high_52w = snapshot.get("52周最高价")
                low_52w = snapshot.get("52周最低价")
                if high_52w and low_52w:
                    text_output += f"   52周区间: {low_52w:.3f} - {high_52w:.3f}\n"
                
                text_output += "\n"
            
            return [TextContent(type="text", text=text_output)]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ 未知工具: {name}\n\n可用工具:\n"
                     f"• get_user_security - 自选股列表\n"
                     f"• get_user_security_group - 自选股分组\n"
                     f"• get_account_info - 账户信息\n"
                     f"• get_positions - 持仓信息\n"
                     f"• 其他高级功能..."
            )]
    
    except Exception as e:
        error_msg = f"调用 {name} 失败: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        
        return [TextContent(
            type="text",
            text=f"❌ {error_msg}\n\n请检查富途客户端状态和网络连接"
        )]

async def run_server():
    """运行服务器"""
    try:
        print("🚀 启动富途修复版MCP服务器...", file=sys.stderr)
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            print("✅ 服务器已启动", file=sys.stderr)
            
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="futu-mcp-enhanced",
                    server_version="2.0.0-fixed",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    ),
                ),
            )
    
    except KeyboardInterrupt:
        print("🛑 服务器被中断", file=sys.stderr)
    except Exception as e:
        print(f"❌ 服务器错误: {e}", file=sys.stderr)
        raise

def main():
    """主函数"""
    try:
        print("🚀 启动富途MCP服务器 v2.0 - 修复版", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        
        # 初始化富途客户端
        if not init_futu_client():
            print("⚠️ 富途客户端初始化失败，将使用受限功能", file=sys.stderr)
        
        # 运行服务器
        asyncio.run(run_server())
        
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止", file=sys.stderr)
    except Exception as e:
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # 清理资源
        if futu_client:
            try:
                futu_client.close()
                print("✅ 富途客户端已关闭", file=sys.stderr)
            except:
                pass

if __name__ == "__main__":
    main() 