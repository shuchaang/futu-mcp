#!/usr/bin/env python3
"""
获取用户自选股列表
"""

import asyncio
import sys
from futu_mcp_server import handle_get_watchlist, handle_get_client_status

async def get_my_watchlist():
    """获取我的自选股列表"""
    print("📊 正在获取你的自选股列表...")
    print("=" * 50)
    
    # 先检查客户端状态
    print("🔍 检查富途客户端连接状态:")
    try:
        status_result = await handle_get_client_status({})
        for content in status_result:
            print(content.text)
        print("-" * 30)
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        print("-" * 30)
    
    # 获取自选股列表
    try:
        # 尝试获取美股自选股
        print("📈 获取美股自选股:")
        result = await handle_get_watchlist({"market": "美股"})
        
        for content in result:
            print(content.text)
            
    except Exception as e:
        print(f"❌ 获取自选股失败: {e}")
        print("\n💡 提示:")
        print("1. 请确保富途牛牛客户端已启动并登录")
        print("2. 请确保已开启API接口")
        print("3. 请确保有自选股设置")

if __name__ == "__main__":
    asyncio.run(get_my_watchlist()) 