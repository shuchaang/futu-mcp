# 富途 MCP 服务器

将富途API客户端功能暴露为 MCP (Model Context Protocol) 工具，允许 AI 助手通过标准化接口访问富途的股票数据。

## 功能特性

- 🔗 **标准化接口**: 通过 MCP 协议提供统一的API访问方式
- 📈 **自选股管理**: 获取富途用户的自选股列表
- ⚙️ **灵活配置**: 支持动态配置富途API连接参数
- 📊 **状态监控**: 实时查看客户端连接状态
- 🛡️ **错误处理**: 完善的错误处理和日志记录

## 安装依赖

### 1. 安装 MCP 库

```bash
pip install mcp
```

### 2. 安装富途SDK（可选，用于实际连接）

```bash
pip install futu-api
```

### 3. 安装其他依赖

```bash
pip install pydantic
```

或者直接安装项目的所有依赖：

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 启动富途客户端

确保富途牛牛客户端已启动并登录，且已开启API接口：

- 打开富途牛牛客户端
- 登录账户
- 在设置中开启API接口（默认端口11111）

### 2. 启动 MCP 服务器

#### 方法一：作为 Python 模块运行（推荐）

```bash
python -m futu_mcp
```

#### 方法二：使用启动脚本

```bash
python futu_mcp/start_futu_mcp.py
```

#### 方法三：直接运行服务器

```bash
python futu_mcp/futu_mcp_server.py
```

### 3. 配置参数（可选）

```bash
# 指定富途API主机和端口
python -m futu_mcp --host 192.168.1.100 --port 11111

# 使用自定义配置文件
python -m futu_mcp --config my_config.json

# 设置日志级别
python -m futu_mcp --log-level DEBUG
```

## 可用工具

### 1. get_watchlist

获取富途用户的自选股列表

**参数:**

- `market` (可选): 市场类型，默认为"美股"，支持["美股", "港股", "A股"]

**示例:**

```json
{
  "market": "美股"
}
```

**返回:**

- 友好格式的自选股列表
- JSON格式的详细数据

### 2. configure_futu_client

配置富途API客户端连接参数

**参数:**

- `host` (必需): 富途API主机地址
- `port` (必需): 富途API端口
- `unlock_pwd` (可选): 解锁密码

**示例:**

```json
{
  "host": "127.0.0.1",
  "port": 11111,
  "unlock_pwd": "your_password"
}
```

### 3. get_client_status

获取富途客户端连接状态和配置信息

**参数:** 无

**返回:**

- 客户端初始化状态
- 连接配置信息
- 最后错误信息（如有）

## 配置文件

### futu_mcp_config.json

```json
{
  "name": "futu-mcp-server",
  "description": "富途API MCP服务器",
  "version": "1.0.0",
  
  "futu_api": {
    "default_host": "127.0.0.1",
    "default_port": 11111,
    "timeout": 30,
    "retry_attempts": 3
  },
  
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/futu_mcp_server.log"
  }
}
```

## 使用示例

### 在 AI 助手中使用

当 MCP 服务器运行后，AI 助手可以通过以下方式调用工具：

1. **获取自选股列表:**

   ```
   请帮我获取美股自选股列表
   ```

2. **配置连接:**

   ```
   请配置富途客户端连接到192.168.1.100:11111
   ```

3. **检查状态:**

   ```
   请检查富途客户端的连接状态
   ```

### 命令行测试

```bash
# 启动服务器（在一个终端）
python -m futu_mcp

# 运行测试脚本验证功能
python futu_mcp/test_mcp.py
```

## 故障排除

### 常见问题

1. **无法连接富途API**
   - 确保富途牛牛客户端已启动并登录
   - 检查API接口是否已开启
   - 验证主机和端口配置是否正确

2. **MCP库导入错误**

   ```bash
   pip install mcp
   ```

3. **富途SDK导入错误**

   ```bash
   pip install futu-api
   ```

4. **权限错误**
   - 确保有足够的权限访问富途API
   - 检查防火墙设置

### 日志查看

```bash
# 查看实时日志
tail -f logs/futu_mcp_server.log

# 启用调试日志
python -m futu_mcp --log-level DEBUG
```

## 扩展功能

### 添加新工具

在 `futu_mcp_server.py` 中添加新的工具：

1. 在 `list_tools()` 函数中添加工具定义
2. 在 `call_tool()` 函数中添加工具处理逻辑
3. 实现具体的处理函数

### 示例：添加股票报价工具

```python
# 在 list_tools() 中添加
Tool(
    name="get_stock_quote",
    description="获取股票实时报价",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码"
            }
        },
        "required": ["symbol"]
    }
)

# 在 call_tool() 中添加处理
elif name == "get_stock_quote":
    return await handle_get_stock_quote(arguments)

# 实现处理函数
async def handle_get_stock_quote(arguments: Dict[str, Any]) -> List[TextContent]:
    # 实现获取股票报价的逻辑
    pass
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 项目地址: [TradeMind](https://github.com/your-repo/trademind)
- 问题反馈: [Issues](https://github.com/your-repo/trademind/issues)
