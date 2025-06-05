# 富途 MCP 服务器

将富途API客户端功能暴露为 MCP (Model Context Protocol) 工具，允许 AI 助手通过标准化接口访问富途的股票数据。

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆或下载项目到本地
cd /Users/admin/Documents/futu/futu_mcp

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装MCP库
pip install git+https://github.com/modelcontextprotocol/python-sdk.git

# 安装其他依赖
pip install -r requirements.txt
```

### 2. 在 Cursor 中配置 MCP

#### 方法一：使用 npx 命令（推荐）

在 Cursor 的 MCP 配置文件中添加以下配置：

```json
{
  "mcpServers": {
    "futu-mcp": {
      "command": "npx",
      "args": [
        "--yes",
        "/Users/admin/Documents/futu/futu_mcp"
      ],
      "env": {
        "FUTU_API_HOST": "127.0.0.1",
        "FUTU_API_PORT": "11111"
      }
    }
  }
}
```

#### 方法二：使用 shell 脚本

```json
{
  "mcpServers": {
    "futu-mcp": {
      "command": "/Users/admin/Documents/futu/futu_mcp/start_mcp_server.sh",
      "args": [],
      "env": {
        "FUTU_API_HOST": "127.0.0.1",
        "FUTU_API_PORT": "11111"
      },
      "cwd": "/Users/admin/Documents/futu/futu_mcp"
    }
  }
}
```

## 🔧 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 | 示例 |
|--------|------|--------|------|
| `FUTU_API_HOST` | 富途API主机地址 | `127.0.0.1` | `192.168.1.100` |
| `FUTU_API_PORT` | 富途API端口 | `11111` | `22222` |
| `FUTU_UNLOCK_PASSWORD` | 富途客户端解锁密码（可选） | - | `your_password` |

### 配置示例

#### 本地默认配置
```json
{
  "env": {
    "FUTU_API_HOST": "127.0.0.1",
    "FUTU_API_PORT": "11111"
  }
}
```

#### 远程服务器配置
```json
{
  "env": {
    "FUTU_API_HOST": "192.168.1.100",
    "FUTU_API_PORT": "11111"
  }
}
```

#### 带解锁密码配置
```json
{
  "env": {
    "FUTU_API_HOST": "127.0.0.1",
    "FUTU_API_PORT": "11111",
    "FUTU_UNLOCK_PASSWORD": "your_unlock_password"
  }
}
```

## 🛠️ 可用工具

### 1. get_watchlist
获取富途用户的自选股列表

**参数:**
- `market` (可选): 市场类型，支持 "美股"、"港股"、"A股"

### 2. configure_futu_client
动态配置富途API客户端连接参数

**参数:**
- `host` (必需): 富途API主机地址
- `port` (必需): 富途API端口
- `unlock_pwd` (可选): 解锁密码

### 3. get_client_status
获取富途客户端连接状态和配置信息

## 🧪 测试

### 命令行测试
```bash
# 激活虚拟环境
source venv/bin/activate

# 使用Node.js启动脚本测试
node bin/futu-mcp.js

# 或使用npx测试
npx /Users/admin/Documents/futu/futu_mcp

# 或使用shell脚本测试
./start_mcp_server.sh
```

### 在 Cursor 中测试
配置完成后，在 Cursor 中可以使用以下命令测试：

1. "请获取我的美股自选股列表"
2. "请检查富途客户端连接状态"
3. "请配置富途客户端连接到192.168.1.100:11111"

## 📁 项目结构

```
futu_mcp/
├── bin/
│   └── futu-mcp.js           # Node.js启动脚本
├── venv/                     # Python虚拟环境
├── futu_mcp_server.py        # MCP服务器主文件
├── start_mcp_server.sh       # Shell启动脚本
├── package.json              # npm包配置
├── requirements.txt          # Python依赖
├── cursor_mcp_config.json    # Cursor配置文件
├── cursor_mcp_config_examples.json  # 配置示例
└── README.md                 # 说明文档
```

## 🔍 故障排除

### 常见问题

1. **虚拟环境不存在**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install git+https://github.com/modelcontextprotocol/python-sdk.git
   pip install -r requirements.txt
   ```

2. **富途客户端连接失败**
   - 确保富途牛牛客户端已启动并登录
   - 检查API接口是否已开启
   - 验证主机和端口配置是否正确

3. **npx 命令找不到包**
   - 确保项目路径正确
   - 检查 package.json 文件是否存在
   - 确保 bin/futu-mcp.js 文件有执行权限

### 日志查看

启动时会显示富途API连接信息：
```
🚀 启动富途 MCP 服务器...
📡 富途API地址: 127.0.0.1:11111
```

## �� 许可证

MIT License 