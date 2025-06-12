#!/usr/bin/env node

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// 获取项目根目录
const projectRoot = path.dirname(__dirname);

// 检查虚拟环境是否存在
const venvPath = path.join(projectRoot, 'venv');
const pythonPath = process.platform === 'win32' 
    ? path.join(venvPath, 'Scripts', 'python.exe')
    : path.join(venvPath, 'bin', 'python');
const pipPath = process.platform === 'win32'
    ? path.join(venvPath, 'Scripts', 'pip')
    : path.join(venvPath, 'bin', 'pip');

// 自动设置虚拟环境函数
function setupVirtualEnv() {
    console.log('⚙️ 首次运行，正在设置Python虚拟环境...');
    
    try {
        // 检查python3是否可用
        try {
            execSync('python3 --version', { stdio: 'pipe' });
        } catch (error) {
            console.error('❌ python3 未找到，请先安装Python 3');
            process.exit(1);
        }
        
        // 创建虚拟环境
        console.log('📦 创建虚拟环境...');
        if (!fs.existsSync(venvPath)) {
            execSync(`python3 -m venv "${venvPath}"`, { 
                cwd: projectRoot, 
                stdio: 'inherit' 
            });
        }
        
        // 安装依赖
        console.log('📦 安装项目依赖...');
        const requirementsPath = path.join(projectRoot, 'requirements.txt');
        if (fs.existsSync(requirementsPath)) {
            execSync(`"${pipPath}" install -r "${requirementsPath}"`, {
                cwd: projectRoot,
                stdio: 'inherit'
            });
        }
        
        console.log('✅ 虚拟环境设置完成！');
        
    } catch (error) {
        console.error('❌ 虚拟环境设置失败:', error.message);
        console.error('\n💡 请手动运行以下命令：');
        console.error(`cd ${projectRoot}`);
        console.error('python3 -m venv venv');
        console.error('source venv/bin/activate');
        console.error('pip install -r requirements.txt');
        process.exit(1);
    }
}

// 检查并设置虚拟环境
if (!fs.existsSync(pythonPath)) {
    setupVirtualEnv();
} else {
    // 确保依赖已安装
    try {
        execSync(`"${pipPath}" freeze`, { stdio: 'pipe' });
    } catch (error) {
        console.log('📦 检测到虚拟环境可能需要更新，正在重新安装依赖...');
        setupVirtualEnv();
    }
}

// 检查MCP服务器文件是否存在
const serverPath = path.join(projectRoot, 'futu_mcp_server.py');
if (!fs.existsSync(serverPath)) {
    console.error('❌ MCP服务器文件不存在:', serverPath);
    process.exit(1);
}

// 设置环境变量
const env = {
    ...process.env,
    PYTHONPATH: projectRoot,
    // 从环境变量获取富途API配置，如果没有则使用默认值
    FUTU_API_HOST: process.env.FUTU_API_HOST || '127.0.0.1',
    FUTU_API_PORT: process.env.FUTU_API_PORT || '11111',
    // 确保 Python 使用虚拟环境中的包
    VIRTUAL_ENV: venvPath,
    PATH: `${path.dirname(pythonPath)}${path.delimiter}${process.env.PATH}`
};

// 如果设置了解锁密码
if (process.env.FUTU_UNLOCK_PASSWORD) {
    env.FUTU_UNLOCK_PASSWORD = process.env.FUTU_UNLOCK_PASSWORD;
}

console.log('🚀 启动富途 MCP 服务器...');
console.log(`📡 富途API地址: ${env.FUTU_API_HOST}:${env.FUTU_API_PORT}`);

// 启动Python MCP服务器
const child = spawn(pythonPath, [serverPath], {
    env: env,
    cwd: projectRoot,
    stdio: 'inherit'
});

// 处理进程退出
child.on('close', (code) => {
    if (code !== 0) {
        console.error(`❌ MCP服务器退出，退出码: ${code}`);
        process.exit(code);
    }
});

// 处理错误
child.on('error', (err) => {
    console.error('❌ 启动MCP服务器失败:', err.message);
    process.exit(1);
});

// 处理进程信号
process.on('SIGINT', () => {
    console.log('\n🛑 正在停止MCP服务器...');
    child.kill('SIGINT');
});

process.on('SIGTERM', () => {
    console.log('\n🛑 正在停止MCP服务器...');
    child.kill('SIGTERM');
}); 