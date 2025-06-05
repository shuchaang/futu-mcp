# 发布富途MCP服务器到npm指南

## 🚀 发布步骤

### 前置条件

1. **npm账户**: 确保你有npm账户
2. **npm CLI**: 确保已安装npm
3. **权限**: 确保你有发布到`@shuchaang`命名空间的权限

### 步骤1：登录npm

```bash
npm login
```

输入你的npm用户名、密码和邮箱。

### 步骤2：检查包名是否可用

```bash
npm view @shuchaang/futu-mcp-server
```

如果显示404错误，说明包名可用。

### 步骤3：确保代码已提交到GitHub

```bash
# 提交所有更改
git add .
git commit -m "准备发布v1.1.0"
git push origin main

# 创建版本标签
git tag v1.1.0
git push origin v1.1.0
```

### 步骤4：发布到npm

```bash
# 发布到npm
npm publish --access public
```

**注意**: `--access public` 是必需的，因为scoped packages默认是私有的。

### 步骤5：验证发布

发布成功后，可以通过以下方式验证：

```bash
# 查看包信息
npm view @shuchaang/futu-mcp-server

# 测试安装
npx @shuchaang/futu-mcp-server
```

## 🔄 更新版本

当你需要发布新版本时：

### 1. 更新版本号

```bash
# 小版本更新 (1.1.0 -> 1.1.1)
npm version patch

# 中版本更新 (1.1.0 -> 1.2.0) 
npm version minor

# 大版本更新 (1.1.0 -> 2.0.0)
npm version major
```

### 2. 推送更改

```bash
git push origin main --tags
```

### 3. 重新发布

```bash
npm publish
```

## 📦 使用已发布的包

发布成功后，用户可以通过以下方式使用：

### 在Cursor中配置

```json
{
  "mcpServers": {
    "futu-mcp": {
      "command": "npx",
      "args": [
        "--yes",
        "@shuchaang/futu-mcp-server"
      ],
      "env": {
        "FUTU_API_HOST": "127.0.0.1",
        "FUTU_API_PORT": "11111"
      }
    }
  }
}
```

### 直接运行

```bash
npx @shuchaang/futu-mcp-server
```

## 🛡️ 安全考虑

1. **敏感信息**: 确保没有在代码中包含任何敏感信息
2. **.npmignore**: 检查.npmignore文件，排除不必要的文件
3. **权限**: 只给必要的人员npm发布权限

## 📊 包统计

发布后，你可以在以下地方查看包的统计信息：

- **npm官网**: https://www.npmjs.com/package/@shuchaang/futu-mcp-server
- **下载统计**: https://npm-stat.com/charts.html?package=@shuchaang/futu-mcp-server

## 🔍 故障排除

### 常见错误

#### 1. "You do not have permission to publish"
**解决方案**: 
- 确保已登录正确的npm账户
- 检查包名是否已被占用
- 如果使用scoped package，确保有该scope的权限

#### 2. "Package name too similar to existing packages"
**解决方案**: 更改包名为更独特的名称

#### 3. "Version already exists"
**解决方案**: 使用`npm version`命令增加版本号

### 调试技巧

```bash
# 检查当前登录用户
npm whoami

# 查看包的详细信息
npm view @shuchaang/futu-mcp-server --json

# 检查将要发布的文件
npm pack --dry-run
```

## 🎯 最佳实践

1. **语义化版本**: 遵循语义化版本规范
2. **变更日志**: 维护CHANGELOG.md文件
3. **测试**: 发布前确保所有测试通过
4. **文档**: 保持README.md更新
5. **标签**: 为每个发布版本创建git标签

## 📈 推广策略

1. **GitHub**: 在README中添加npm徽章
2. **社区**: 在相关社区分享
3. **文档**: 提供详细的使用文档
4. **示例**: 提供完整的使用示例

---

发布成功后，你的富途MCP服务器就可以被全世界的开发者使用了！🎉 