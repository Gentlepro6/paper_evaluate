from sqlalchemy import Column, Integer, Float, Text, DateTime, String
from datetime import datetime
from .base import Base

class Evaluation(Base):
    """论文评价表"""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, nullable=False)
    score = Column(Float)
    comments = Column(Text)
    model_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"Evaluation(id={self.id}, paper_id={self.paper_id}, score={self.score})"
