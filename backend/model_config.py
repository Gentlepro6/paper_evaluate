from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .base import Base

class ModelConfig(Base):
    """模型配置表"""
    __tablename__ = "model_config"

    id = Column(Integer, primary_key=True, index=True)
    server_url = Column(String(255), nullable=True)
    default_model = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=False, default=0.3)
    max_tokens = Column(Integer, nullable=False, default=2000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"ModelConfig(id={self.id}, default_model={self.default_model}, temperature={self.temperature}, max_tokens={self.max_tokens})"

    @classmethod
    def get_default_config(cls):
        """获取默认配置"""
        return {
            "server_url": "http://localhost:11434",
            "default_model": "qwen2.5:14b",
            "temperature": 0.3,
            "max_tokens": 2000
        }
