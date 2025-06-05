#!/usr/bin/env python3
"""
获取用户持仓信息
"""

import asyncio
import sys
from futu_mcp_server import handle_get_positions, handle_get_account_info, handle_get_client_status

async def get_my_positions():
    """获取我的持仓信息"""
    print("💰 正在获取你的持仓信息...")
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
    
    # 尝试获取模拟账户信息
    print("💳 获取模拟账户信息:")
    try:
        account_result = await handle_get_account_info({"account_type": "SIMULATE"})
        for content in account_result:
            print(content.text)
        print("-" * 30)
    except Exception as e:
        print(f"❌ 获取账户信息失败: {e}")
        print("-" * 30)
    
    # 获取持仓信息
    print("📊 获取模拟账户持仓:")
    try:
        result = await handle_get_positions({"account_type": "SIMULATE"})
        
        for content in result:
            print(content.text)
            
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        print("\n💡 提示:")
        print("1. 持仓查询需要交易权限，请确保富途客户端已登录")
        print("2. 如果使用真实账户，可能需要解锁密码")
        print("3. 确认已开启交易API权限")
        print("4. 模拟账户可能需要先在富途客户端中开通")

if __name__ == "__main__":
    asyncio.run(get_my_positions()) 