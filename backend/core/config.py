from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "学术论文评价系统"
    DEBUG: bool = True
    
    # 数据库配置
    MODEL_DATABASE_URL: str = "sqlite:///./databases/model/model.db"
    PAPER_DATABASE_URL: str = "sqlite:///./databases/paper/paper.db"
    KNOWLEDGE_DATABASE_URL: str = "sqlite:///./databases/knowledge/knowledge.db"
    EVALUATE_DATABASE_URL: str = "sqlite:///./databases/evaluate/evaluate.db"
    
    # Ollama配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "llama2"  # 默认使用 llama2 模型
    REQUIRED_MODELS: list = ["llama2"]  # 需要安装的模型
    
    # 文件存储路径
    PAPERS_DIR: str = "data/papers"
    KNOWLEDGE_DIR: str = "data/knowledge"
    LOGS_DIR: str = "logs"
    
    # 向量维度配置
    VECTOR_DIMENSION: int = 768
    
    # 评分配置
    MIN_SCORE: int = 65
    MAX_SCORE: int = 98
    
    # 支持的文件类型
    SUPPORTED_FILE_TYPES: list = [".pdf", ".doc", ".docx"]
    
    class Config:
        env_file = ".env"

settings = Settings()

# 论文类型配置
PAPER_TYPES = {
    "undergraduate": "本科论文",
    "master": "硕士论文",
    "phd": "博士论文"
}

# 支持的文件类型
SUPPORTED_FILE_TYPES = [".pdf", ".doc", ".docx"]

# OCR配置
OCR_LANGUAGES = ["chi_sim", "eng"]  # 支持中文和英文
