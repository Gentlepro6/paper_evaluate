from backend.database import init_db, ModelSessionLocal, ModelConfig, Base, model_engine
from backend.database import Paper, Evaluation  # 导入Paper和Evaluation模型
from backend.knowledge import KnowledgeBase  # 显式导入KnowledgeBase类
import logging
import os
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_directories():
    """确保所有必要的目录结构存在"""
    logger.info("确保必要的目录结构存在...")
    directories = [
        # 数据库目录
        "backend/databases/model",
        "backend/databases/paper",
        "backend/databases/knowledge",
        "backend/databases/evaluate",
        # 数据目录
        "data/papers/undergraduate",
        "data/papers/master",
        "data/papers/phd",
        "data/papers/evaluation/temp",
        "data/knowledge",
        "data/temp",
        "data/uploads",
        # 后端内部数据目录
        "backend/data/papers/undergraduate",
        "backend/data/papers/master",
        "backend/data/papers/phd",
        "backend/data/papers/evaluation",
        "backend/data/knowledge",
        # 日志目录
        "logs",
        # 模型目录
        "models"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # 创建.gitkeep文件以确保空目录被Git跟踪
        gitkeep_file = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, "w") as f:
                pass
    
    logger.info("目录结构创建完成")

def init_database():
    # 确保目录结构存在
    ensure_directories()
    
    logger.info("创建数据库表...")
    # 在所有数据库中创建相应的表
    init_db()
    
    # 显式创建 knowledge_base 表
    logger.info("显式创建 knowledge_base 表...")
    try:
        # 确保 KnowledgeBase 类被注册到元数据中
        KnowledgeBase.__table__.create(bind=model_engine, checkfirst=True)
        logger.info("knowledge_base 表创建成功")
    except Exception as e:
        logger.error(f"创建 knowledge_base 表失败: {str(e)}")
    
    # 初始化默认配置
    db = ModelSessionLocal()
    try:
        logger.info("检查模型配置...")
        config = db.query(ModelConfig).first()
        if not config:
            logger.info("创建默认模型配置...")
            default_config = ModelConfig(**ModelConfig.get_default_config())
            db.add(default_config)
            db.commit()
            logger.info("默认模型配置创建成功")
        else:
            logger.info("模型配置已存在")
        
        # 检查是否需要创建初始Paper记录
        paper_count = db.query(Paper).count()
        if paper_count == 0:
            logger.info("创建初始Paper记录...")
            # 为每种论文类型创建一个空记录，确保前端加载不会失败
            paper_types = ["undergraduate", "master", "phd"]
            for paper_type in paper_types:
                dummy_paper = Paper(
                    title=f"示例{paper_type}论文",
                    file_path=f"data/papers/{paper_type}/.gitkeep",
                    paper_type=paper_type,
                    status="pending",
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now()
                )
                db.add(dummy_paper)
            db.commit()
            logger.info("初始Paper记录创建成功")
        
        # 检查是否需要创建初始KnowledgeBase记录
        kb_count = db.query(KnowledgeBase).count()
        if kb_count == 0:
            logger.info("创建初始KnowledgeBase记录...")
            dummy_kb = KnowledgeBase(
                title="示例知识库文档",
                file_path="data/knowledge/.gitkeep",
                language="zh",
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            db.add(dummy_kb)
            db.commit()
            logger.info("初始KnowledgeBase记录创建成功")
        
        # 检查是否需要创建初始Evaluation记录
        eval_count = db.query(Evaluation).count()
        if eval_count == 0:
            # 获取所有Paper记录的ID
            paper_records = db.query(Paper).all()
            paper_ids = [paper.id for paper in paper_records]
            logger.info(f"找到的Paper记录ID: {paper_ids}")
            
            if paper_ids:  # 确保有Paper记录可用
                paper_id = paper_ids[0]  # 使用第一个Paper记录
                logger.info(f"创建初始Evaluation记录，关联到Paper ID: {paper_id}...")
                
                # 获取该Paper的详细信息
                paper = db.query(Paper).filter(Paper.id == paper_id).first()
                logger.info(f"关联论文信息: id={paper.id}, title={paper.title}, type={paper.paper_type}")
                
                dummy_eval = Evaluation(
                    paper_id=paper_id,
                    comments="这是系统初始化时创建的示例评价记录，您可以进行真实评价替换它。",
                    score=80,
                    model_name="system_init",
                    created_at=datetime.datetime.now()
                )
                db.add(dummy_eval)
                db.commit()
                logger.info(f"初始Evaluation记录创建成功: id={dummy_eval.id}, paper_id={dummy_eval.paper_id}")
            else:
                logger.warning("没有找到Paper记录，无法创建初始Evaluation记录")
            
    except Exception as e:
        db.rollback()
        logger.error(f"初始化数据失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("开始初始化数据库...")
    init_database()
    logger.info("数据库初始化完成")
