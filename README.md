# 学术论文评价系统

这是一个基于Web的学术论文智能评价系统，采用现代化技术架构，结合大语言模型能力，可以对本科、硕士和博士论文进行全方位、多维度的智能评价和分析。本系统旨在提高学术评价效率，为教育机构、研究单位和学术期刊提供客观、专业的论文质量评估工具。

## 系统架构

本系统采用前后端分离的现代化架构设计：

- **前端**：基于Node.js构建的响应式Web界面，提供直观的用户交互体验
- **后端**：Python FastAPI框架，提供高性能API服务和数据处理能力
- **数据库**：SQLite轻量级数据库，支持高效的数据存储和查询
- **AI引擎**：集成Ollama大模型，提供智能分析和评价能力
- **文档处理**：结合多种PDF解析和OCR技术，实现论文内容的精准提取

## 主要功能

### 论文分析
- 支持PDF格式论文上传和分析，自动处理多种排版格式
- 智能提取论文标题、摘要、关键词、章节结构等关键信息
- 自动识别论文类型（研究型/综述型）和学术级别（本科/硕士/博士）
- 基于深度学习的文本分析，提取研究方法、实验设计和结论要点

### 评价系统
- 基于Ollama大模型的智能评价引擎，支持多种模型选择（llama2, qwen等）
- 全面的多维度评分系统：
  - 学术评价（原创性、创新点、文献综述质量、研究方法合理性、论证逻辑等）
  - 会议评价（研究会议适配性、知识产权保护、数据安全与伦理考量等）
  - 技术分析（概念化程度、实证支持充分性、数据质量与可靠性、技术路线等）
  - 格式评价（呈现清晰度、组织结构合理性、写作质量、参考文献规范性等）
- 自适应评分标准，根据不同学科领域和论文类型动态调整评价维度
- 详细的评价报告生成，包含具体改进建议和参考示例

### 知识库管理
- 智能知识库构建与维护，支持向量化存储和语义检索
- 多层次论文分类管理（学科领域/研究方向/学位类型）
- 参考文献智能关联与引用网络分析
- 学术热点追踪与研究趋势分析
- 基于相似度的相关论文推荐系统

### 结果导出
- 支持多种格式导出（PDF/Word/Excel/HTML）
- 丰富的评价报告模板，支持自定义模板设计
- 批量导出与处理功能，适合大规模论文评审
- 评价结果可视化展示，包含图表和数据分析
- 支持评价历史记录追踪与比对分析

## 系统要求

### 软件要求
- Python 3.8+
- Node.js 16+
- Ollama（用于本地大模型接入）
- Tesseract OCR（用于PDF文本识别）
- Poppler（用于PDF处理）

### 硬件要求
- CPU: 4核心以上
- 内存: 16GB以上
- 硬盘空间: 20GB以上（用于模型和数据存储）

### 支持的操作系统
- Linux（Ubuntu 20.04+）
- macOS（Catalina 10.15+）
- Windows 10/11（需要WSL2）

## 安装指南

本项目提供了一键安装脚本，可以自动完成所有安装步骤。详细的安装说明请参考项目根目录下的 **INSTALL.md** 文件。

### 快速安装

1. 安装系统依赖

   #### Ubuntu/Debian
   ```bash
   # 安装 Tesseract OCR
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr
   sudo apt-get install -y tesseract-ocr-chi-sim  # 中文支持

   # 安装 Poppler
   sudo apt-get install -y poppler-utils
   ```

   #### macOS
   ```bash
   # 使用 Homebrew 安装
   brew install tesseract
   brew install tesseract-lang  # 语言包
   brew install poppler
   ```

2. 安装 Ollama

   访问 [Ollama 官网](https://ollama.ai) 下载并安装。

3. 克隆项目
   ```bash
   git clone [项目地址]
   cd paper_evaluate
   ```

4. 运行一键安装脚本
   ```bash
   # 给脚本添加执行权限
   chmod +x setup_project.sh
   
   # 运行安装脚本
   ./setup_project.sh
   ```

   该脚本将自动完成以下操作：
   - 创建并激活 Python 虚拟环境
   - 安装所有 Python 依赖
   - 初始化数据库
   - 安装前端依赖
   - 创建必要的目录结构
   - 生成默认配置文件

> 注意：如果您希望手动安装，或遇到安装问题，请参考 INSTALL.md 文件中的详细说明。

## 运行系统

### 1. 启动 Ollama 服务
```bash
# 确保 Ollama 已经启动并运行
ollama serve

# 在新终端中拉取所需模型（默认使用 llama2）
ollama pull llama2
```

### 2. 使用启动脚本运行系统

安装完成后，可以使用项目根目录下的启动脚本一键启动系统：

```bash
# 给脚本添加执行权限
chmod +x start_app.sh

# 运行启动脚本
./start_app.sh
```

该脚本将自动启动后端和前端服务。

### 3. 手动启动服务（可选）

如果您希望手动启动服务，可以按照以下步骤操作：

```bash
# 启动后端服务
# 在项目根目录下
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

cd backend
uvicorn main:app --reload
```

```bash
# 在新终端中启动前端服务
cd frontend
npm start
```

系统将在以下地址运行：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- Ollama 服务：http://localhost:11434

### 配置环境变量

如果使用 `setup_project.sh` 脚本安装，它将自动创建默认的 `.env` 文件。如果需要手动配置，可以编辑该文件：

```bash
# 编辑环境变量文件
vim .env  # 或使用任何文本编辑器
```

主要配置项包括：
- `MODEL_DATABASE_URL`: 模型数据库连接地址
- `PAPER_DATABASE_URL`: 论文数据库连接地址
- `KNOWLEDGE_DATABASE_URL`: 知识库数据库连接地址
- `EVALUATE_DATABASE_URL`: 评价数据库连接地址
- `OLLAMA_BASE_URL`: Ollama API 地址
- `DEFAULT_MODEL`: 默认使用的模型名称

## 项目清理与部署

### 项目清理

如果您需要清理项目（例如在上传到GitHub之前），可以使用项目根目录下的 `clean_project.py` 脚本：

```bash
# 查看将要删除的文件（不实际删除）
python clean_project.py --dry-run --verbose

# 执行实际清理
python clean_project.py
```

该脚本将删除不必要的文件，如虚拟环境、数据库文件、前端依赖等，但保留项目结构和必要的代码文件。

### 打包部署

#### 1. 构建前端生产版本
```bash
# 进入前端目录
cd frontend

# 构建生产版本
npm run build
```

#### 2. 创建部署包
```bash
# 在项目根目录下

# 创建部署目录
mkdir -p dist

# 复制必要文件
cp -r backend dist/
cp -r frontend/build dist/frontend
cp requirements.txt dist/
cp .env dist/
cp setup_project.sh dist/
cp start_app.sh dist/

# 打包为 zip 文件
cd dist
zip -r ../paper_evaluate.zip .
cd ..
```

#### 3. 部署说明

1. 解压 `paper_evaluate.zip` 到目标服务器

2. 使用安装脚本安装项目：
   ```bash
   chmod +x setup_project.sh
   ./setup_project.sh
   ```

3. 启动服务：
   ```bash
   # 启动 Ollama
   ollama serve
   
   # 拉取所需模型
   ollama pull llama2
   
   # 启动应用
   chmod +x start_app.sh
   ./start_app.sh
   ```

4. 配置 Nginx（用于生产环境，可选）：
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;
   
       location / {
           root /path/to/frontend/build;
           try_files $uri $uri/ /index.html;
       }
   
       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
```

## 退出应用

### 1. 停止前端服务
```bash
# 在运行前端的终端中按 Ctrl+C
```

### 2. 停止后端服务
```bash
# 在运行后端的终端中按 Ctrl+C

# 退出虚拟环境
deactivate
```

### 3. 停止 Ollama 服务
```bash
# 在 macOS/Linux 下
pkill ollama

# 或者在 Ollama 的终端中按 Ctrl+C
```

### 1. 启动 Ollama 服务
```bash
ollama serve
```

### 2. 启动后端服务
```bash
# 激活虚拟环境（如果未激活）
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端服务
```bash
cd frontend
npm run dev
```

启动后可以访问：
- 前端页面：`http://localhost:3000`
- API 文档：`http://localhost:8000/docs`

2. 启动前端服务
```bash
cd frontend
npm start
```

## 项目结构

```
Paper_evaluation/
├── backend/           # 后端代码
│   ├── api/          # API路由
│   ├── core/         # 核心功能
│   ├── models/       # 数据模型
│   └── utils/        # 工具函数
├── frontend/         # 前端代码
├── data/            # 数据存储
│   ├── papers/      # 论文存储
│   └── knowledge/   # 知识库存储
└── logs/            # 日志文件
```

## 使用说明

详细使用说明请参考[使用文档]。

## 日志

系统运行日志位于`logs/`目录下，包含详细的运行记录和错误信息。
