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

### 📈 行情数据工具

#### 1. get_watchlist
获取富途用户的自选股列表

**参数:**
- `market` (可选): 市场类型，支持 "美股"、"港股"、"A股"

#### 2. get_stock_quote
获取股票实时报价信息

**参数:**
- `stock_code` (必需): 股票代码，如 'AAPL', 'HK.00700', 'SZ.000001'
- `market` (可选): 市场类型，支持 "US", "HK", "SH", "SZ"

#### 3. get_stock_history
获取股票历史K线数据

**参数:**
- `stock_code` (必需): 股票代码
- `period` (可选): K线周期，支持 "1min", "5min", "15min", "30min", "60min", "day", "week", "month"
- `count` (可选): 获取数据条数，默认30条

#### 4. search_stock
搜索股票，根据股票名称或代码查找相关股票

**参数:**
- `keyword` (必需): 搜索关键词，可以是股票名称或代码
- `market` (可选): 搜索市场，支持 "US", "HK", "SH", "SZ", "ALL"
- `limit` (可选): 返回结果数量限制，默认10条

#### 5. get_market_snapshot
获取市场快照，包括主要指数和热门股票

**参数:**
- `market` (可选): 市场类型，支持 "US", "HK", "CN"

### 💰 交易相关工具（需要交易权限）

#### 6. get_account_info
获取账户信息，包括资产、持仓等

**参数:**
- `account_type` (可选): 账户类型，支持 "REAL", "SIMULATE"

#### 7. get_positions
获取持仓信息

**参数:**
- `account_type` (可选): 账户类型，支持 "REAL", "SIMULATE"

### ⚙️ 配置工具

#### 8. configure_futu_client
动态配置富途API客户端连接参数

**参数:**
- `host` (必需): 富途API主机地址
- `port` (必需): 富途API端口
- `unlock_pwd` (可选): 解锁密码

#### 9. get_client_status
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

#### 基础功能测试
1. "请获取我的美股自选股列表"
2. "请检查富途客户端连接状态"
3. "请配置富途客户端连接到192.168.1.100:11111"

#### 行情数据测试
4. "请获取苹果公司(AAPL)的实时报价"
5. "请获取腾讯(HK.00700)最近30天的日K线数据"
6. "请搜索包含'特斯拉'的股票"
7. "请获取美股市场快照"

#### 交易功能测试（需要交易权限）
8. "请获取我的模拟账户信息"
9. "请查看我的持仓情况"

#### 使用示例

**获取股票报价:**
```
请获取苹果公司的实时报价
```

**获取历史数据:**
```
请获取腾讯控股最近20天的日K线数据
```

**搜索股票:**
```
请搜索名称包含"阿里巴巴"的股票
```

**查看账户信息:**
```
请获取我的模拟账户资金情况
```

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