# Cursor中配置富途MCP服务器指南

## 🚀 快速配置

### 1. 基础配置（推荐）

将以下配置添加到Cursor的MCP配置文件中：

```json
{
  "mcpServers": {
    "futu-mcp": {
      "command": "npx",
      "args": [
        "--yes",
        "@shuchang/futu-mcp-server@latest"
      ],
      "env": {
        "FUTU_API_HOST": "127.0.0.1",
        "FUTU_API_PORT": "11111"
      }
    }
  }
} 
```


### 2. 带交易功能的配置

如果你需要使用交易功能（账户信息、持仓查询），添加解锁密码：

```json
{
  "mcpServers": {
    "futu-mcp": {
      "command": "npx",
      "args": [
        "--yes",
        "@shuchang/futu-mcp-server@latest"
      ],
      "env": {
        "FUTU_API_HOST": "127.0.0.1",
        "FUTU_API_PORT": "11111",
        "FUTU_UNLOCK_PASSWORD": "your_unlock_password"
      }
    }
  }
}
```
