#!/usr/bin/env python3
"""
富途 MCP 服务器启动脚本

使用方法:
    python start_futu_mcp.py [--host HOST] [--port PORT] [--config CONFIG_FILE]

示例:
    python start_futu_mcp.py
    python start_futu_mcp.py --host 192.168.1.100 --port 11111
    python start_futu_mcp.py --config custom_config.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging(log_level="INFO", log_file=None):
    """设置日志配置"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 创建日志目录
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def load_config(config_file="futu_mcp_config.json"):
    """加载配置文件"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"警告: 配置文件 {config_file} 不存在，使用默认配置")
        return {
            "futu_api": {
                "default_host": "127.0.0.1",
                "default_port": 11111
            },
            "logging": {
                "level": "INFO"
            }
        }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 无法加载配置文件 {config_file}: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="启动富途 MCP 服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                                    # 使用默认配置启动
  %(prog)s --host 192.168.1.100              # 指定富途API主机
  %(prog)s --port 11111                       # 指定富途API端口
  %(prog)s --config custom_config.json       # 使用自定义配置文件
  %(prog)s --log-level DEBUG                  # 设置日志级别
        """
    )
    
    parser.add_argument(
        '--host',
        default=None,
        help='富途API主机地址 (默认: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='富途API端口 (默认: 11111)'
    )
    
    parser.add_argument(
        '--config',
        default='futu_mcp_config.json',
        help='配置文件路径 (默认: futu_mcp_config.json)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=None,
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        default=None,
        help='日志文件路径 (默认: 仅控制台输出)'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置环境变量
    if args.host:
        os.environ['FUTU_HOST'] = args.host
    elif 'futu_api' in config:
        os.environ['FUTU_HOST'] = str(config['futu_api'].get('default_host', '127.0.0.1'))
    
    if args.port:
        os.environ['FUTU_PORT'] = str(args.port)
    elif 'futu_api' in config:
        os.environ['FUTU_PORT'] = str(config['futu_api'].get('default_port', 11111))
    
    # 设置日志
    log_level = args.log_level or config.get('logging', {}).get('level', 'INFO')
    log_file = args.log_file or config.get('logging', {}).get('file')
    
    setup_logging(log_level, log_file)
    
    logger = logging.getLogger(__name__)
    
    # 显示启动信息
    logger.info("=" * 60)
    logger.info("富途 MCP 服务器启动")
    logger.info("=" * 60)
    logger.info(f"配置文件: {args.config}")
    logger.info(f"富途API主机: {os.environ.get('FUTU_HOST', '127.0.0.1')}")
    logger.info(f"富途API端口: {os.environ.get('FUTU_PORT', '11111')}")
    logger.info(f"日志级别: {log_level}")
    if log_file:
        logger.info(f"日志文件: {log_file}")
    logger.info("=" * 60)
    
    # 检查依赖
    try:
        import futu
        logger.info("✅ 富途SDK已安装")
    except ImportError:
        logger.warning("⚠️  富途SDK未安装，某些功能可能无法使用")
        logger.info("安装命令: pip install futu-api")
    
    try:
        import mcp
        logger.info("✅ MCP库已安装")
    except ImportError:
        logger.error("❌ MCP库未安装，无法启动服务器")
        logger.info("安装命令: pip install mcp")
        sys.exit(1)
    
    # 启动服务器
    try:
        logger.info("正在启动 MCP 服务器...")
        
        # 导入并运行服务器
        from .futu_mcp_server import main
        import asyncio
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止服务器...")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)
    finally:
        logger.info("富途 MCP 服务器已停止")


if __name__ == "__main__":
    main() 