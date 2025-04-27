# 论文评价系统安装指南

本文档提供了论文评价系统的详细安装和设置指南。请按照以下步骤进行操作，确保系统正确安装和配置。

## 快速安装

我们提供了一键安装脚本，可以自动完成所有安装步骤：

```bash
# 给脚本添加执行权限
chmod +x setup_project.sh

# 运行安装脚本
./setup_project.sh
```

该脚本将自动创建虚拟环境、安装依赖、初始化数据库和设置目录结构。如果您希望手动安装，请参考下面的详细步骤。

## 系统要求

- Python 3.8+
- Node.js 14+
- npm 6+
- Ollama（用于本地大模型接入）
- 足够的磁盘空间用于存储模型和论文文件（建议至少20GB）

## 手动安装 - 后端

如果您选择手动安装，请按照以下步骤操作：

1. 创建并激活虚拟环境（推荐）：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. 创建必要的目录结构：

```bash
# 数据库目录
mkdir -p backend/databases/model
mkdir -p backend/databases/paper
mkdir -p backend/databases/knowledge
mkdir -p backend/databases/evaluate

# 数据存储目录
mkdir -p data/papers
mkdir -p data/knowledge
mkdir -p data/temp
mkdir -p data/uploads

# 日志目录
mkdir -p logs
```

4. 初始化数据库：

```bash
cd backend
python init_db.py
cd ..
```

   如果遇到`ModuleNotFoundError`错误，请确保您已正确安装所有依赖，特别是SQLAlchemy和pydantic-settings。

4. 启动后端服务：

```bash
cd ..  # 回到项目根目录
uvicorn backend.main:app --reload
```

后端服务将在 http://localhost:8000 运行。

## 手动安装 - 前端

1. 安装前端依赖：

```bash
cd frontend

# 使用自动安装脚本（推荐）
chmod +x setup_frontend.sh
./setup_frontend.sh

# 或者手动安装依赖
npm install
npm install --save-dev @testing-library/jest-dom @testing-library/react @testing-library/user-event
npm install --save-dev typescript @types/node @types/react @types/react-dom @types/jest
```

2. 启动前端开发服务器：

```bash
npm start
```

前端将在 http://localhost:3000 运行。

## 首次运行
在项目目录下执行 ./start_app.sh

1. 系统首次运行时需要下载嵌入模型，这可能需要一些时间。
2. 您需要上传一些论文到知识库和各类型论文库中（本科、硕士、博士）。
3. 每个类别至少需要5篇论文才能开始评价。

## 环境变量配置

系统使用 `.env` 文件进行配置。您可以复制`.env.example`文件（如果存在）或创建新的`.env`文件，主要参数包括：

- `MODEL_DATABASE_URL`：模型数据库连接字符串（默认为`sqlite:///./databases/model/model.db`）
- `PAPER_DATABASE_URL`：论文数据库连接字符串
- `KNOWLEDGE_DATABASE_URL`：知识库数据库连接字符串
- `EVALUATE_DATABASE_URL`：评价数据库连接字符串
- `OLLAMA_BASE_URL`：Ollama API地址（默认为`http://localhost:11434`）
- `DEFAULT_MODEL`：默认使用的模型名称（如`llama2`）
- `UPLOAD_DIR`：上传文件存储目录
- `ALLOWED_EXTENSIONS`：允许上传的文件类型
- `MAX_TOKENS`：生成评价的最大token数
- `TEMPERATURE`：生成评价的随机性参数

## 注意事项

1. 首次运行时需要安装Ollama并下载相应的模型：
   ```bash
   # 安装Ollama（请访问 https://ollama.ai 下载安装包）
   # 启动Ollama服务
   ollama serve
   # 在新终端中拉取所需模型
   ollama pull llama2
   ```

2. 系统需要足够的内存来加载和运行模型（建议至少16GB内存）。

3. 评价论文需要论文库和知识库各至少有5个文档作为参考。

4. 如果您从GitHub克隆项目，请注意项目不包含虚拟环境、数据库文件和前端依赖，这是为了保持仓库大小较小。使用`setup_project.sh`脚本可以自动安装所有需要的组件。

5. 如果您需要清理项目（例如在上传到GitHub之前），可以使用项目根目录下的`clean_project.py`脚本：
   ```bash
   # 查看将要删除的文件（不实际删除）
   python clean_project.py --dry-run --verbose
   # 执行实际清理
   python clean_project.py
   ```

6. 项目采用了以下策略来减小仓库大小：
   - 分离前端依赖：仅保留核心依赖的描述，其他依赖在安装时下载
   - 不包含虚拟环境和数据库文件：这些文件在安装时生成
   - 不包含模型和大文件：这些文件在首次运行时下载

## 问题排查

如果遇到问题，请检查：

1. 所有依赖是否正确安装
2. 数据库是否正确初始化
3. Ollama服务是否正在运行
4. 日志文件中是否有错误信息

## 目录结构

```
Paper_Evaluate/
├── alembic/            # 数据库迁移文件
├── backend/            # 后端代码
│   ├── api/            # API路由
│   ├── core/           # 核心配置（包含系统配置）
│   ├── databases/      # 数据库文件存储目录
│   │   ├── model/      # 模型数据库
│   │   ├── paper/      # 论文数据库
│   │   ├── knowledge/  # 知识库数据库
│   │   └── evaluate/   # 评价数据库
│   ├── knowledge.py    # 知识库模型
│   ├── database.py     # 数据库模型和连接
│   ├── init_db.py      # 数据库初始化脚本
│   └── main.py         # 主应用入口
├── data/               # 数据存储
│   ├── knowledge_base/ # 知识库文档
│   ├── undergraduate/  # 本科论文
│   ├── master/         # 硕士论文
│   ├── phd/            # 博士论文
│   ├── temp/           # 临时文件
│   └── uploads/        # 上传文件
├── frontend/           # 前端代码
│   ├── node_modules/   # 前端依赖（安装后生成）
│   ├── public/         # 静态资源
│   └── src/            # 源代码
├── logs/               # 日志文件
├── venv/               # Python虚拟环境（安装后生成）
├── .env                # 环境变量配置
├── clean_project.py    # 项目清理脚本
├── requirements.txt    # Python依赖
└── start_app.sh        # 应用启动脚本
```

## 常见问题解决

1. **数据库初始化失败**
   - 确保已创建必要的数据库目录
   - 检查SQLAlchemy和其他依赖是否正确安装
   - 检查导入路径是否正确
   - 如果遇到`from models.database import ...`的错误，请将其修改为`from database import ...`

2. **Ollama模型加载失败**
   - 确保Ollama服务正在运行
   - 检查是否已成功拉取所需模型
   - 检查网络连接和防火墙设置
   - 如果拉取模型速度过慢，可以尝试使用代理或更换网络环境

3. **前端依赖安装失败**
   - 尝试使用`npm cache clean --force`清理npm缓存
   - 检查Node.js和npm版本是否符合要求
   - 尝试使用`npm install --legacy-peer-deps`安装依赖
   - 如果某些依赖安装失败，可以尝试单独安装它们

4. **脚本权限问题**
   - 确保所有脚本有执行权限：
     ```bash
     chmod +x setup_project.sh
     chmod +x frontend/setup_frontend.sh
     chmod +x start_app.sh
     ```

5. **仓库大小问题**
   - 如果您需要将项目上传到GitHub，但发现大小过大，请先运行清理脚本：
     ```bash
     python clean_project.py --force
     ```
   - 确保`.gitignore`文件正确配置，忽略虚拟环境、依赖和大文件
