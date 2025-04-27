from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from backend.base import Base

class KnowledgeBase(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    language = Column(String(50))  # 'zh', 'en', 'zh-en'
    vector = Column(Text, nullable=True)  # 向量数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"KnowledgeBase(id={self.id}, title={self.title}, language={self.language})"
