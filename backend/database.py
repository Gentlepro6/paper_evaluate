from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from backend.core.config import settings
import enum

# 创建数据库引擎
model_engine = create_engine(settings.MODEL_DATABASE_URL)
paper_engine = create_engine(settings.PAPER_DATABASE_URL)
knowledge_engine = create_engine(settings.KNOWLEDGE_DATABASE_URL)
evaluate_engine = create_engine(settings.EVALUATE_DATABASE_URL)

# 创建会话工厂
ModelSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=model_engine)
PaperSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=paper_engine)
KnowledgeSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=knowledge_engine)
EvaluateSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=evaluate_engine)

# 为兼容现有代码，保留原来的SessionLocal
SessionLocal = ModelSessionLocal

Base = declarative_base()

class PaperType(enum.Enum):
    undergraduate = "undergraduate"
    master = "master"
    phd = "phd"

class Paper(Base):
    """论文信息表"""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    paper_type = Column(Enum(PaperType), nullable=False)
    status = Column(String(50), default='pending')  # pending, evaluated
    vector = Column(Text)  # 存储向量的JSON字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class Evaluation(Base):
    """论文评价表"""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, nullable=False)
    score = Column(Float)
    comments = Column(Text)
    model_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelConfig(Base):
    """模型配置表"""
    __tablename__ = "model_config"

    id = Column(Integer, primary_key=True, index=True)
    server_url = Column(String(255), nullable=True)  # 允许为空，使用默认服务器
    default_model = Column(String(100), nullable=True)  # 允许为空，使用默认模型
    temperature = Column(Float, nullable=False, default=0.3)
    max_tokens = Column(Integer, nullable=False, default=2000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"ModelConfig(id={self.id}, server_url='{self.server_url}', default_model='{self.default_model}', "\
               f"temperature={self.temperature}, max_tokens={self.max_tokens})"

    @classmethod
    def get_default_config(cls):
        return {
            "server_url": settings.OLLAMA_BASE_URL,
            "default_model": settings.DEFAULT_MODEL,
            "temperature": 0.3,
            "max_tokens": 2000
        }

# 导入其他模型
from backend.knowledge import KnowledgeBase

# 创建所有表
def init_db():
    # 只创建不存在的表，不删除现有的表
    # 由于所有数据库URL都指向同一个数据库文件，所以只需要在model_engine上创建所有表
    Base.metadata.create_all(bind=model_engine)  # 在同一个数据库中创建所有表
    
    # 初始化默认的模型配置（如果不存在）
    db = ModelSessionLocal()
    try:
        config = db.query(ModelConfig).first()
        if not config:
            default_config = ModelConfig(**ModelConfig.get_default_config())
            db.add(default_config)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f'初始化模型配置失败: {str(e)}')
    finally:
        db.close()

# 获取数据库会话
def get_model_db():
    db = ModelSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_paper_db():
    db = PaperSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_knowledge_db():
    db = KnowledgeSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_evaluate_db():
    db = EvaluateSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 为兼容现有代码，保留原来的get_db
def get_db():
    db = ModelSessionLocal()
    try:
        yield db
    finally:
        db.close()
