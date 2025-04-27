from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import logging
from datetime import datetime

from backend.database import get_db as get_knowledge_db, Base
from backend.knowledge import KnowledgeBase
from backend.utils.document_processor import DocumentProcessor
from backend.utils.vector_store import VectorStore
from backend.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# 初始化向量存储
try:
    vector_store = VectorStore()
    if not vector_store.model or not vector_store.index:
        logger.error('向量存储初始化失败，模型或索引未加载')
except Exception as e:
    logger.error(f'初始化向量存储失败: {str(e)}')

@router.get("/knowledge")
async def get_knowledge_list(db: Session = Depends(get_knowledge_db)):
    """获取知识库文档列表"""
    try:
        logger.info("开始获取知识库列表")
        try:
            knowledge_list = db.query(KnowledgeBase).all()
            logger.info(f"找到 {len(knowledge_list)} 条知识库记录")
            for k in knowledge_list:
                logger.info(f"知识库记录: id={k.id}, title={k.title}, language={k.language}")
        except Exception as e:
            logger.error(f"查询知识库列表失败: {str(e)}")
            raise
        return {
            "files": [
                {
                    "id": k.id,
                    "title": k.title,
                    "language": k.language,
                    "created_at": k.created_at.isoformat() if k.created_at else None
                }
                for k in knowledge_list
            ]
        }
    except Exception as e:
        logger.error(f"获取知识库列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取知识库列表失败")

@router.post("/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    db: Session = Depends(get_knowledge_db)
):
    """上传知识库文档"""
    try:
        # 获取文件类型
        file_type = os.path.splitext(file.filename)[1].lower()
        if file_type not in ['.pdf', '.doc', '.docx']:
            raise HTTPException(status_code=400, detail="只支持 PDF、DOC、DOCX 格式的文件")

        # 获取完整的路径
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        save_dir = os.path.join(base_dir, settings.KNOWLEDGE_DIR)
        os.makedirs(save_dir, exist_ok=True)
        logger.info(f"创建知识库目录: {save_dir}")

        # 保存文件
        file_path = os.path.join(save_dir, file.filename)
        logger.info(f"开始保存文件: {file_path}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 处理文档
        logger.info("开始处理文档内容")
        processor = DocumentProcessor()
        text = processor.process_document(file_path)
        
        # 生成向量
        logger.info("开始生成文档向量")
        try:
            vector_id = vector_store.add_document(text, {"file_path": file_path})
            logger.info(f"向量生成成功，ID: {vector_id}")
        except Exception as e:
            logger.error(f"向量生成失败: {str(e)}")
            os.remove(file_path)  # 清理文件
            raise HTTPException(status_code=500, detail="向量生成失败")

        # 保存到数据库
        knowledge = KnowledgeBase(
            title=file.filename,
            file_path=file_path,
            language='zh',  # 默认为中文
            vector=text
        )
        db.add(knowledge)
        db.commit()
        db.refresh(knowledge)
        
        logger.info(f"知识库文档上传成功: {knowledge.id}")
        return {"id": knowledge.id, "title": knowledge.title}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"知识库文档上传失败: {str(e)}")
        # 清理文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="知识库文档上传失败")

@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: int, db: Session = Depends(get_knowledge_db)):
    """删除知识库文档"""
    try:
        knowledge = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 删除文件
        if os.path.exists(knowledge.file_path):
            os.remove(knowledge.file_path)

        # 删除数据库记录
        db.delete(knowledge)
        db.commit()

        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除知识库文档失败")
