#!/bin/bash

# 检查并清理已存在的进程
cleanup() {
    echo "清理已存在的进程..."
    # 清理后端进程
    if lsof -i:8000 > /dev/null; then
        lsof -i:8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
    fi
    # 清理前端进程
    if lsof -i:3000 > /dev/null; then
        lsof -i:3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
    fi
}

# 初始化数据库
init_database() {
    echo "初始化数据库..."
    source venv/bin/activate
    python -m backend.init_db
    echo "数据库初始化完成"
}

# 启动后端服务
start_backend() {
    echo "启动后端服务..."
    source venv/bin/activate
    # 从项目根目录启动，避免导入路径问题
    python -m uvicorn backend.main:app --reload &
    sleep 3  # 等待后端启动
}

# 启动前端服务
start_frontend() {
    echo "启动前端服务..."
    cd frontend
    npm start &
    cd ..
}

# 主流程
echo "=== 启动论文评价系统 ==="

# 清理已存在的进程
cleanup

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 初始化数据库
init_database

# 启动服务
start_backend
start_frontend

echo "=== 系统启动完成 ==="
echo "前端访问地址: http://localhost:3000"
echo "后端API地址: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户输入
wait
