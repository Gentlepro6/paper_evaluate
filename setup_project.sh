#!/bin/bash
# 论文评价系统初始化脚本
# 此脚本用于在克隆仓库后自动设置整个项目

echo "===== 论文评价系统初始化 ====="
echo "此脚本将自动设置项目环境，包括创建虚拟环境、安装依赖和初始化数据库。"
echo

# 确保我们在项目根目录
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 创建必要的目录
echo "创建必要的目录结构..."
mkdir -p backend/databases/model
mkdir -p backend/databases/paper
mkdir -p backend/databases/knowledge
mkdir -p backend/databases/evaluate
mkdir -p data/papers
mkdir -p data/knowledge
mkdir -p data/temp
mkdir -p data/uploads
mkdir -p logs

# 创建Python虚拟环境
echo "创建Python虚拟环境..."
python -m venv venv

# 激活虚拟环境
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # macOS或Linux
    source venv/bin/activate
    PYTHON_CMD="python"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
    PYTHON_CMD="python"
else
    echo "无法识别的操作系统，请手动激活虚拟环境。"
    PYTHON_CMD="python"
fi

# 安装Python依赖
echo "安装Python依赖..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt

# 确保依赖正确安装
echo "确保关键依赖已安装..."
$PYTHON_CMD -m pip install sqlalchemy==2.0.28 pydantic-settings==2.2.1

# 初始化数据库
echo "初始化数据库..."
cd backend
$PYTHON_CMD init_db.py
cd $PROJECT_ROOT

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
chmod +x setup_frontend.sh
./setup_frontend.sh
cd $PROJECT_ROOT

# 创建.env文件（如果不存在）
if [ ! -f .env ]; then
    echo "创建默认.env配置文件..."
    cat > .env << EOL
# 数据库配置
MODEL_DATABASE_URL=sqlite:///./backend/databases/model/model.db
PAPER_DATABASE_URL=sqlite:///./backend/databases/paper/paper.db
KNOWLEDGE_DATABASE_URL=sqlite:///./backend/databases/knowledge/knowledge.db
EVALUATE_DATABASE_URL=sqlite:///./backend/databases/evaluate/evaluate.db

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama2

# 文件存储路径
PAPERS_DIR=data/papers
KNOWLEDGE_DIR=data/knowledge
LOGS_DIR=logs

# 评分配置
MIN_SCORE=65
MAX_SCORE=98
EOL
fi

# 确保启动脚本有执行权限
chmod +x start_app.sh

echo
echo "===== 初始化完成 ====="
echo "您现在可以使用以下命令启动应用："
echo "  ./start_app.sh"
echo
echo "注意：首次运行前，请确保已安装并启动Ollama服务，并拉取所需模型："
echo "  ollama serve"
echo "  ollama pull llama2"
echo
