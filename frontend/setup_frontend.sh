#!/bin/bash
# 前端依赖安装脚本
# 此脚本用于安装前端所需的所有依赖

echo "开始安装前端依赖..."

# 确保我们在前端目录中
cd "$(dirname "$0")"

# 清理npm缓存
echo "清理npm缓存..."
npm cache clean --force

# 安装ajv依赖
echo "安装ajv依赖..."
npm install --save-dev --legacy-peer-deps ajv@^6.12.6

# 安装核心依赖
echo "安装核心依赖..."
npm install --legacy-peer-deps

# 安装开发依赖
echo "安装开发依赖..."
npm install --save-dev --legacy-peer-deps @testing-library/jest-dom @testing-library/react @testing-library/user-event
npm install --save-dev --legacy-peer-deps typescript@4.9.5 @types/node @types/react @types/react-dom @types/jest

# 修复可能的依赖问题
echo "修复依赖问题..."
npm install --save-dev --legacy-peer-deps ajv-keywords@^3.5.2

echo "前端依赖安装完成！"
