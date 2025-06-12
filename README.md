# @shuchang/futu-mcp-server

富途API MCP服务器 - 完整的股票数据和交易功能MCP工具集

## 快速开始

使用 npx 直接运行（推荐）：

```bash
npx @shuchang/futu-mcp-server
```

或者全局安装：

```bash
npm install -g @shuchang/futu-mcp-server
futu-mcp
```

## 环境变量配置

可以通过环境变量配置富途API连接参数：

- `FUTU_API_HOST`: 富途API主机地址（默认：127.0.0.1）
- `FUTU_API_PORT`: 富途API端口（默认：11111）
- `FUTU_UNLOCK_PASSWORD`: 交易解锁密码（可选）

示例：

```bash
export FUTU_API_HOST=192.168.1.100
export FUTU_API_PORT=12345
export FUTU_UNLOCK_PASSWORD=your_password
npx @shuchang/futu-mcp-server
```

## 功能特点

- 自动设置Python虚拟环境
- 自动安装所需依赖
- 支持环境变量配置
- 完整的富途API功能支持
- MCP协议集成

## 系统要求

- Node.js >= 14.0.0
- Python 3.x
- 富途牛牛客户端 