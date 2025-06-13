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

# Futu MCP 使用指南

## 1. 功能介绍

### 1.1 行情查询
- 获取实时报价和盘口数据
- 查看K线数据（支持分钟、日、周、月K线）
- 获取股票快照数据（价格、成交量、市值等）
- 条件选股功能（支持财务指标、技术指标筛选）

### 1.2 交易功能
- 查看持仓信息
- 查看账户资金
- 股票交易（买入/卖出）
- 订单管理（改单/撤单）

### 1.3 自选股管理
- 获取自选股列表
- 查看自选股分组
- 管理自选股分组

## 2. 配置说明

### 2.1 环境要求
- 需要安装并运行 Futu OpenD
- 需要有效的 Futu 账户
- 需要相应的 API 权限

### 2.2 权限配置
1. 登录 Futu 账户
2. 打开 Futu OpenD
3. 配置 API 权限：
   - 行情权限
   - 交易权限（如需要）
   - 自选股权限

### 2.3 接口配置
```go
// 示例配置
{
    "FutuOpenD": {
        "Host": "localhost",
        "Port": 11111,
        "EnableEncrypt": true
    },
    "Market": ["HK", "US", "CN"],
    "Language": "zh-CN"
}
```

## 3. 权限说明

### 3.1 行情权限
- 基础行情：所有用户均可使用
- Level 2 行情：需要开通相应市场的 Level 2 行情权限
- 期权行情：需要开通期权市场权限

### 3.2 交易权限
- 查询权限：可查看持仓、资金等信息
- 交易权限：可进行买入、卖出等操作
- 需要在 Futu OpenD 中配置相应的交易密码和权限

### 3.3 自选股权限
- 读取权限：可查看自选股列表和分组
- 修改权限：可修改自选股分组和内容

## 4. 新增功能

### 4.1 条件选股增强
- 新增技术指标筛选
- 支持多个条件组合
- 支持自定义筛选条件保存

### 4.2 交易功能优化
- 支持条件单
- 支持止盈止损设置
- 订单状态实时推送

### 4.3 数据分析功能
- K线数据分析
- 成交量分析
- 技术指标计算

### 4.4 使用示例

```go
// 获取持仓信息
positions, err := client.GetPositions(ctx, &futu.GetPositionsRequest{
    AccountType: futu.AccountType_REAL
})

// 获取账户资金
funds, err := client.GetFunds(ctx, &futu.GetFundsRequest{
    TrdEnv: futu.TrdEnv_REAL
})

// 条件选股示例
filter, err := client.GetStockFilter(ctx, &futu.GetStockFilterRequest{
    Market: "HK",
    FilterList: []futu.StockFilter{
        {
            FieldName: "VOLUME",
            FilterMin: 1000000,
            FilterMax: 10000000,
        },
    },
})
```

## 注意事项

1. 请确保 Futu OpenD 正常运行
2. 使用交易功能前请仔细确认账户和权限设置
3. 注意遵守各市场的交易规则和时间
4. 建议在进行实盘交易前先使用模拟交易测试
5. 请妥善保管账户密码和交易密码

## 常见问题

1. 无法连接 Futu OpenD
   - 检查 OpenD 是否正常运行
   - 检查网络连接
   - 确认配置信息是否正确

2. 交易权限相关
   - 确认是否配置交易密码
   - 检查是否有相应市场的交易权限
   - 确认账户状态是否正常

3. 行情数据延迟
   - 检查网络连接质量
   - 确认是否订阅了相应的行情权限
   - 检查 OpenD 的性能状态

## 更新日志

### v1.0.0
- 基础功能实现
- 支持行情查询
- 支持基础交易功能

### v1.1.0
- 新增条件选股功能
- 优化交易接口
- 添加数据分析功能

### v1.2.0
- 新增止盈止损功能
- 优化数据推送机制
- 增加更多技术指标支持 