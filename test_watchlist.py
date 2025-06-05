#!/usr/bin/env python3
"""
测试获取自选股列表功能
"""

import asyncio
import sys
from futu_mcp_server import handle_get_watchlist

async def test_get_watchlist():
    """测试获取自选股列表"""
    print("🔍 正在测试获取自选股列表功能...")
    
    try:
        # 测试获取美股自选股
        result = await handle_get_watchlist({"market": "美股"})
        
        print("\n📈 自选股列表测试结果:")
        print("=" * 50)
        
        for content in result:
            print(content.text)
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_get_watchlist()) 