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

**注意**: 请将路径 `/Users/admin/Documents/futu/futu_mcp` 替换为你的实际项目路径。

### 2. 带交易功能的配置

如果你需要使用交易功能（账户信息、持仓查询），添加解锁密码：

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
        "FUTU_API_PORT": "11111",
        "FUTU_UNLOCK_PASSWORD": "your_unlock_password"
      }
    }
  }
}
```

### 3. 远程富途客户端配置

如果富途客户端运行在其他机器上：

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
        "FUTU_API_HOST": "192.168.1.100",
        "FUTU_API_PORT": "11111"
      }
    }
  }
}
```

## 📁 配置文件位置

### macOS
```
~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.cursor-small-model/settings.json
```

### Windows
```
%APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.cursor-small-model\settings.json
```

### Linux
```
~/.config/Cursor/User/globalStorage/rooveterinaryinc.cursor-small-model\settings.json
```

## 🔧 详细配置步骤

### 步骤1：准备环境

1. **确保富途牛牛客户端已启动并登录**
2. **开启API接口**：
   - 在富途牛牛客户端中，点击"设置" → "API接口" → "开启API接口"
   - 记录API端口号（通常是11111）

### 步骤2：验证MCP服务器

在项目目录中运行测试：

```bash
# 进入项目目录
cd /Users/admin/Documents/futu/futu_mcp

# 激活虚拟环境
source venv/bin/activate

# 测试npx启动
npx --yes /Users/admin/Documents/futu/futu_mcp
```

### 步骤3：配置Cursor

1. **打开Cursor的MCP配置文件**
2. **添加富途MCP配置**（选择上面的配置之一）
3. **保存文件**
4. **重启Cursor**

### 步骤4：验证配置

重启Cursor后，你应该能够使用以下命令：

#### 基础功能测试
- "请获取我的自选股列表"
- "请检查富途客户端连接状态"

#### 行情数据测试
- "请获取苹果公司(AAPL)的实时报价"
- "请获取腾讯控股(HK.00700)最近30天的日K线数据"
- "请搜索包含'特斯拉'的股票"
- "请获取美股市场快照"

#### 交易功能测试（需要解锁密码）
- "请获取我的模拟账户信息"
- "请查看我的持仓情况"

## 🛠️ 可用工具列表

配置成功后，你将拥有以下9个工具：

### 📈 行情数据工具
1. **get_watchlist** - 获取自选股列表
2. **get_stock_quote** - 获取股票实时报价
3. **get_stock_history** - 获取历史K线数据
4. **search_stock** - 搜索股票
5. **get_market_snapshot** - 获取市场快照

### 💰 交易工具（需要解锁密码）
6. **get_account_info** - 获取账户信息
7. **get_positions** - 获取持仓信息

### ⚙️ 配置工具
8. **configure_futu_client** - 配置客户端连接
9. **get_client_status** - 获取连接状态

## 🔍 故障排除

### 常见问题

#### 1. "找不到npx命令"
**解决方案**: 确保已安装Node.js
```bash
# 安装Node.js (macOS)
brew install node

# 验证安装
node --version
npm --version
```

#### 2. "Python虚拟环境不存在"
**解决方案**: 重新创建虚拟环境
```bash
cd /Users/admin/Documents/futu/futu_mcp
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
pip install -r requirements.txt
```

#### 3. "富途API连接失败"
**解决方案**: 检查富途客户端
- 确保富途牛牛客户端已启动并登录
- 检查API接口是否已开启
- 验证主机和端口配置是否正确
- 确保防火墙没有阻止连接

#### 4. "MCP服务器无响应"
**解决方案**: 检查配置
- 验证项目路径是否正确
- 检查环境变量设置
- 查看Cursor的错误日志
- 重启Cursor

#### 5. "交易功能无法使用"
**解决方案**: 检查交易权限
- 确保已设置正确的解锁密码
- 验证富途账户是否有交易权限
- 检查是否使用了正确的账户类型（REAL/SIMULATE）

### 调试技巧

#### 1. 查看详细日志
```bash
# 手动启动MCP服务器查看日志
cd /Users/admin/Documents/futu/futu_mcp
source venv/bin/activate
python futu_mcp_server.py
```

#### 2. 测试单个功能
```bash
# 测试富途API连接
python -c "
import futu as ft
quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)
print('连接成功')
quote_ctx.close()
"
```

#### 3. 验证环境变量
```bash
# 检查环境变量
echo $FUTU_API_HOST
echo $FUTU_API_PORT
```

## 📚 使用示例

### 获取股票报价
```
用户: 请获取苹果公司的实时报价
AI: 我来为您获取苹果公司(AAPL)的实时报价信息...
```

### 分析股票趋势
```
用户: 请获取特斯拉最近20天的日K线数据，并分析趋势
AI: 我来获取特斯拉(TSLA)的历史数据并进行趋势分析...
```

### 搜索股票
```
用户: 请搜索所有包含"阿里"的股票
AI: 我来搜索包含"阿里"的相关股票...
```

### 查看投资组合
```
用户: 请查看我的持仓情况和盈亏状态
AI: 我来获取您的持仓信息...
```

## 🔄 更新和维护

### 更新MCP服务器
```bash
cd /Users/admin/Documents/futu/futu_mcp
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

### 更新富途API
```bash
source venv/bin/activate
pip install --upgrade futu-api
```

## 🎯 最佳实践

1. **开发环境**: 优先使用模拟账户进行测试
2. **安全性**: 不要在配置文件中硬编码敏感信息
3. **性能**: 避免频繁调用API，合理使用缓存
4. **监控**: 定期检查连接状态和API调用情况
5. **备份**: 定期备份配置文件和重要数据

---

配置完成后，你就可以在Cursor中享受强大的富途股票数据和交易功能了！🚀 