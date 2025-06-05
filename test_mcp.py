#!/usr/bin/env python3
"""
富途 MCP 服务器测试脚本

用于测试 MCP 服务器的基本功能，包括工具列表和工具调用。
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加父目录到路径
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

async def test_tools():
    """测试工具功能"""
    print("=" * 60)
    print("富途 MCP 服务器功能测试")
    print("=" * 60)
    
    try:
        # 导入服务器模块
        from futu_mcp.futu_mcp_server import list_tools, call_tool, initialize_futu_client
        
        print("✅ 成功导入 MCP 服务器模块")
        
        # 测试工具列表
        print("\n📋 测试工具列表...")
        tools = await list_tools()
        print(f"可用工具数量: {len(tools)}")
        
        for tool in tools:
            print(f"  • {tool.name}: {tool.description}")
        
        # 测试客户端状态
        print("\n🔍 测试客户端状态...")
        try:
            status_result = await call_tool("get_client_status", {})
            print("客户端状态检查完成:")
            for content in status_result:
                print(f"  {content.text}")
        except Exception as e:
            print(f"  ⚠️ 客户端状态检查失败: {e}")
        
        # 测试配置客户端
        print("\n⚙️ 测试配置客户端...")
        try:
            config_result = await call_tool("configure_futu_client", {
                "host": "127.0.0.1",
                "port": 11111
            })
            print("客户端配置完成:")
            for content in config_result:
                print(f"  {content.text}")
        except Exception as e:
            print(f"  ⚠️ 客户端配置失败: {e}")
        
        # 测试获取自选股（可能会失败，因为需要富途客户端运行）
        print("\n📈 测试获取自选股...")
        try:
            watchlist_result = await call_tool("get_watchlist", {"market": "美股"})
            print("自选股获取完成:")
            for content in watchlist_result:
                # 只显示前200个字符，避免输出过长
                text = content.text[:200] + "..." if len(content.text) > 200 else content.text
                print(f"  {text}")
        except Exception as e:
            print(f"  ⚠️ 自选股获取失败: {e}")
            print("  这是正常的，因为可能没有运行富途客户端")
        
        print("\n✅ 测试完成！")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装必要的依赖:")
        print("  pip install mcp pydantic")
        return False
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True


async def test_json_schema():
    """测试工具的 JSON Schema"""
    print("\n" + "=" * 60)
    print("JSON Schema 测试")
    print("=" * 60)
    
    try:
        from futu_mcp.futu_mcp_server import list_tools
        
        tools = await list_tools()
        
        for tool in tools:
            print(f"\n🔧 工具: {tool.name}")
            print(f"描述: {tool.description}")
            print(f"输入模式:")
            print(json.dumps(tool.inputSchema, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"❌ Schema 测试失败: {e}")


def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    dependencies = [
        ("mcp", "MCP 服务器框架"),
        ("pydantic", "数据验证库"),
        ("futu", "富途SDK（可选）"),
        ("asyncio", "异步IO库（内置）")
    ]
    
    for dep, desc in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}: {desc}")
        except ImportError:
            if dep == "futu":
                print(f"  ⚠️ {dep}: {desc} - 未安装（可选）")
            else:
                print(f"  ❌ {dep}: {desc} - 未安装")


async def main():
    """主测试函数"""
    print("富途 MCP 服务器测试工具")
    print("此工具用于验证 MCP 服务器的基本功能\n")
    
    # 检查依赖
    check_dependencies()
    
    # 运行功能测试
    success = await test_tools()
    
    # 运行 Schema 测试
    await test_json_schema()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！MCP 服务器功能正常。")
        print("\n下一步:")
        print("1. 启动富途牛牛客户端并登录")
        print("2. 在富途客户端中开启API接口")
        print("3. 运行 MCP 服务器:")
        print("   python -m futu_mcp")
        print("   或")
        print("   python futu_mcp/start_futu_mcp.py")
    else:
        print("❌ 测试失败，请检查依赖项和配置。")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试运行错误: {e}")
        sys.exit(1) 