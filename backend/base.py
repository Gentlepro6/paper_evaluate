from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from backend.core.config import settings

# 创建基础模型类
Base = declarative_base()

# 创建数据库引擎和会话
def create_db_engine(database_url: str):
    return create_engine(database_url)

def create_db_session(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建各个模块的数据库引擎和会话
model_engine = create_db_engine(settings.MODEL_DATABASE_URL)
paper_engine = create_db_engine(settings.PAPER_DATABASE_URL)
knowledge_engine = create_db_engine(settings.KNOWLEDGE_DATABASE_URL)
evaluate_engine = create_db_engine(settings.EVALUATE_DATABASE_URL)

ModelSession = create_db_session(model_engine)
PaperSession = create_db_session(paper_engine)
KnowledgeSession = create_db_session(knowledge_engine)
EvaluateSession = create_db_session(evaluate_engine)

# 获取数据库会话的函数
def get_model_db():
    db = ModelSession()
    try:
        yield db
    finally:
        db.close()

def get_paper_db():
    db = PaperSession()
    try:
        yield db
    finally:
        db.close()

def get_knowledge_db():
    db = KnowledgeSession()
    try:
        yield db
    finally:
        db.close()

def get_evaluate_db():
    db = EvaluateSession()
    try:
        yield db
    finally:
        db.close()

# 初始化所有数据库
def init_all_db():
    Base.metadata.create_all(bind=model_engine)
    Base.metadata.create_all(bind=paper_engine)
    Base.metadata.create_all(bind=knowledge_engine)
    Base.metadata.create_all(bind=evaluate_engine)
