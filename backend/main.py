from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.api import paper_routes, model_routes, knowledge_routes
from backend.database import init_db as init_all_db
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="学术论文评价系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在开发环境中允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建必要的目录
def create_required_directories():
    directories = [
        'data/papers/undergraduate',
        'data/papers/master',
        'data/papers/phd',
        'data/papers/evaluation',
        'data/papers/evaluation/temp',  # 添加评价临时目录
        'data/knowledge',
        'logs'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"确保目录存在: {directory}")

@app.on_event("startup")
async def startup_event():
    """
    应用启动时的初始化操作
    """
    try:
        # 创建必要的目录
        create_required_directories()
        
        # 初始化所有数据库
        from backend.database import init_db as init_all_db, get_db as get_model_db, get_db as get_paper_db, get_db as get_knowledge_db, get_db as get_evaluate_db
        from backend.database import ModelConfig, Paper, Evaluation
        from backend.knowledge import KnowledgeBase
        init_all_db()
        
        # 确保模型目录存在
        models_dir = os.path.abspath('./models')
        os.makedirs(models_dir, exist_ok=True)
        logger.info(f'检查模型目录: {models_dir}')
        
        # 检查向量模型是否存在
        try:
            # 预先初始化向量存储，触发模型检查和下载
            from backend.utils.vector_store import VectorStore
            vector_store = VectorStore()
            if vector_store.model and vector_store.index:
                logger.info('向量模型检查成功，模型已存在或已下载')
            else:
                logger.warning('向量模型初始化失败，知识库搜索功能可能不可用')
        except Exception as e:
            logger.error(f'检查向量模型时发生错误: {str(e)}')
        
        # 检查数据库连接
        model_db = next(get_model_db())
        paper_db = next(get_paper_db())
        knowledge_db = next(get_knowledge_db())
        evaluate_db = next(get_evaluate_db())
        
        try:
            # 检查模型配置
            config = model_db.query(ModelConfig).first()
            if config:
                logger.info(f'加载模型配置: {config}')
            else:
                logger.warning('未找到模型配置，将使用默认配置')
            
            # 检查各个模块的数据量
            knowledge_count = knowledge_db.query(KnowledgeBase).count()
            paper_count = paper_db.query(Paper).count()
            evaluation_count = evaluate_db.query(Evaluation).count()
            logger.info(f'知识库文档数量: {knowledge_count}')
            logger.info(f'论文数量: {paper_count}')
            logger.info(f'评价记录数量: {evaluation_count}')
            
        finally:
            model_db.close()
            paper_db.close()
            knowledge_db.close()
            evaluate_db.close()
            
        logger.info('系统初始化完成')
        
    except Exception as e:
        logger.error(f'系统初始化失败: {str(e)}')
        raise
    
    
    logger.info("应用启动完成")

# 包含路由模块
app.include_router(paper_routes.router, prefix="/api", tags=["papers"])
app.include_router(model_routes.router, prefix="/api", tags=["models"])
app.include_router(knowledge_routes.router, prefix="/api", tags=["knowledge"])

@app.get("/")
async def root():
    """
    根路由，用于测试API是否正常运行
    """
    return {"status": "ok", "message": "API服务运行正常"}

@app.get("/api/health")
async def health_check():
    """
    健康检查路由
    """
    return {"status": "ok", "message": "服务正常"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
