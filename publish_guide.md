# 发布富途MCP到npm指南

## 📦 发布前准备

### 1. 注册npm账号
```bash
npm adduser
# 或
npm login
```

### 2. 修改package.json
确保包名唯一（可能需要改名）：
```json
{
  "name": "@your-username/futu-mcp-server",
  "version": "1.0.0"
}
```

### 3. 添加.npmignore文件
```bash
# 创建.npmignore，排除不需要的文件
echo "venv/
*.pyc
__pycache__/
.git/
.DS_Store
test_mcp.py
cursor_mcp_config*.json" > .npmignore
```

## 🚀 发布步骤

### 1. 测试本地安装
```bash
npm pack
npm install -g ./your-package-name-1.0.0.tgz
```

### 2. 发布到npm
```bash
# 公开发布
npm publish --access public

# 或私有发布（需要付费账号）
npm publish
```

### 3. 验证发布
```bash
npx @your-username/futu-mcp-server@latest
```

## 🔄 更新版本

```bash
# 更新版本号
npm version patch  # 1.0.0 -> 1.0.1
npm version minor  # 1.0.0 -> 1.1.0
npm version major  # 1.0.0 -> 2.0.0

# 重新发布
npm publish
```

## 📋 发布后的使用方式

用户可以这样使用：

```json
{
  "mcpServers": {
    "futu-mcp": {
      "command": "npx",
      "args": ["-y", "@your-username/futu-mcp-server@latest"],
      "env": {
        "FUTU_API_HOST": "127.0.0.1",
        "FUTU_API_PORT": "11111"
      }
    }
  }
}
```

## ⚠️ 注意事项

1. **Python依赖**: 用户需要有Python环境
2. **富途客户端**: 用户需要安装富途牛牛客户端
3. **网络访问**: 首次使用需要下载包
4. **版本管理**: 定期更新版本以修复bug和添加功能 