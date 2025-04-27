from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import os
import shutil
import aiofiles
from pydantic import BaseModel
from backend.database import Base, Paper, PaperType, get_db as get_paper_db
from backend.database import ModelConfig, get_db as get_model_db
from backend.database import get_db as get_evaluate_db, Evaluation
from backend.database import get_db as get_knowledge_db
from backend.knowledge import KnowledgeBase
from backend.utils.document_processor import DocumentProcessor
from backend.utils.vector_store import VectorStore
from backend.utils.ollama_client import OllamaClient
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 初始化向量存储
vector_store = VectorStore()
ollama_client = OllamaClient()

class EvaluationResponse(BaseModel):
    id: int
    paperId: int
    fileName: str
    title: str
    paperType: str
    modelName: str = ""
    score: float = 0.0
    comments: str = ""
    timestamp: Optional[str] = None

class EvaluationsResponse(BaseModel):
    evaluations: List[EvaluationResponse]

@router.get("/papers/evaluations", response_model=EvaluationsResponse)
async def get_all_evaluations(evaluate_db: Session = Depends(get_evaluate_db), paper_db: Session = Depends(get_paper_db)):
    """
    获取所有论文的评价历史
    """
    try:
        logger.info('开始获取评价历史')
        result = []
        
        try:
            # 获取所有评价
            evaluations = evaluate_db.query(Evaluation).order_by(Evaluation.created_at.desc()).all()
            logger.info(f'找到 {len(evaluations)} 条评价记录')
            for eval in evaluations:
                logger.info(f'评价记录详情: id={eval.id}, paper_id={eval.paper_id}, score={eval.score}, model={eval.model_name}')
            
            if not evaluations:
                logger.info('没有找到评价记录')
                return {"evaluations": []}
            
            # 获取所有的论文ID
            paper_ids = [eval.paper_id for eval in evaluations]
            logger.info(f'需要查找的论文ID: {paper_ids}')
            
            # 获取评价对应的论文
            papers = {}
            if paper_ids:
                papers = {paper.id: paper for paper in paper_db.query(Paper).filter(Paper.id.in_(paper_ids)).all()}
            logger.info(f'找到 {len(papers)} 篇相关论文')
            for paper_id, paper in papers.items():
                logger.info(f'论文详情: id={paper_id}, title={paper.title}, type={paper.paper_type}')
            
            # 格式化返回数据
            for eval in evaluations:
                try:
                    paper = papers.get(eval.paper_id)
                    if not paper:
                        logger.warning(f'论文 {eval.paper_id} 不存在，跳过此评价记录')
                        continue
                        
                    # 确保所有字段都有默认值
                    try:
                        # 处理 paper_type
                        try:
                            paper_type = paper.paper_type.value if hasattr(paper.paper_type, 'value') else str(paper.paper_type)
                        except Exception as e:
                            logger.warning(f'获取 paper_type 失败: {str(e)}, 使用默认值 undergraduate')
                            paper_type = 'undergraduate'
                        logger.info(f'处理 paper_type: {paper_type}')
                        
                        # 处理 score
                        try:
                            score = float(eval.score) if eval.score is not None else 0.0
                        except Exception as e:
                            logger.warning(f'转换 score 失败: {str(e)}, 使用默认值 0.0')
                            score = 0.0
                        logger.info(f'处理 score: {score}')
                        
                        # 处理 timestamp
                        try:
                            timestamp = eval.created_at.isoformat() if eval.created_at else None
                        except Exception as e:
                            logger.warning(f'转换 timestamp 失败: {str(e)}, 使用默认值 None')
                            timestamp = None
                        logger.info(f'处理 timestamp: {timestamp}')
                        
                        evaluation_data = {
                            "id": eval.id,
                            "paperId": eval.paper_id,
                            "fileName": paper.title,
                            "title": paper.title,
                            "paperType": paper_type,
                            "modelName": eval.model_name if eval.model_name else "",
                            "score": score,
                            "comments": eval.comments if eval.comments else "",
                            "timestamp": timestamp
                        }
                        
                        logger.debug(f'处理评价记录: {evaluation_data}')
                        result.append(evaluation_data)
                        
                    except Exception as e:
                        logger.error(f'格式化评价数据时出错: {str(e)}')
                        raise
                    
                except Exception as e:
                    logger.error(f'处理评价记录时出错: {str(e)}')
                    logger.exception(e)
                    continue
                    
            logger.info(f'返回数据: {result}')
            
            return {"evaluations": result}
        except Exception as e:
            logger.error(f'查询数据库时出错: {str(e)}')
            logger.exception(e)
            raise HTTPException(
                status_code=500,
                detail=f'查询数据库失败: {str(e)}'
            )
    except Exception as e:
        logger.error(f'获取评价历史失败: {str(e)}')
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f'获取评价历史失败: {str(e)}'
        )

@router.post("/papers/upload/{paper_type}")
async def upload_paper(
    paper_type: PaperType,
    file: UploadFile = File(...),
    paper_db: Session = Depends(get_paper_db)
):
    """
    上传论文文件
    """
    try:
        logger.info(f"开始处理文件上传: {file.filename}, 类型: {paper_type.value}")
        
        # 检查文件类型
        if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="只支持 PDF、DOC、DOCX 格式的文件"
            )

        # 检查文件大小
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="文件太大，请上传小于10MB的文件"
            )
            
        # 获取完整的路径
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        papers_dir = os.path.join(base_dir, settings.PAPERS_DIR)
        paper_type_dir = os.path.join(papers_dir, paper_type.value)
        
        # 创建目录
        os.makedirs(paper_type_dir, exist_ok=True)
        logger.debug(f"创建论文目录: {paper_type_dir}")
        
        # 检查文件是否已存在
        file_path = os.path.join(paper_type_dir, file.filename)
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"文件 '{file.filename}' 已存在于{paper_type.value}目录中"
            )

        await file.seek(0)

        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        # 处理文档
        logger.debug(f"开始提取文档内容: {file_path}")
        try:
            text = DocumentProcessor.process_document(file_path)
            logger.info(f"文档内容提取成功，长度: {len(text)}")
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            # 删除已上传的文件
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"文档处理失败: {str(e)}")
        
        # 生成向量
        logger.debug("开始生成文档向量")
        try:
            doc_id = vector_store.add_document(text, {
                "file_path": file_path,
                "paper_type": paper_type.value
            })
            logger.info(f"向量生成成功，ID: {doc_id}")
        except Exception as e:
            logger.error(f"向量生成失败: {str(e)}")
            # 删除已上传的文件
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"向量生成失败: {str(e)}")
        
        # 保存到数据库
        logger.debug("开始保存到数据库")
        try:
            paper = Paper(
                title=os.path.splitext(file.filename)[0],
                file_path=file_path,
                paper_type=paper_type,
                vector=str(doc_id),
                status='pending'  # 添加状态字段，表示未评价
            )
            paper_db.add(paper)
            paper_db.commit()
            logger.info(f"论文保存成功，ID: {paper.id}")
            
            return {"id": paper.id, "message": "论文上传成功"}
            
        except ValueError as e:
            logger.error(f'论文保存失败: {str(e)}')
            paper_db.rollback()
            # 删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=str(e))
            
        except HTTPException as e:
            logger.error(f'论文保存失败: {e.detail}')
            paper_db.rollback()
            # 删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
        except Exception as e:
            logger.error(f'论文保存过程发生未知错误: {str(e)}')
            paper_db.rollback()
            # 删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            paper_db.rollback()
            raise HTTPException(status_code=500, detail=f'论文保存失败: {str(e)}')
        
        return {"id": paper.id, "title": paper.title, "message": "论文上传成功"}
    
    except ValueError as e:
        logger.error(f'论文上传失败: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException as e:
        logger.error(f'论文上传失败: {e.detail}')
        raise e
    except Exception as e:
        logger.error(f'论文上传过程发生未知错误: {str(e)}')
        raise HTTPException(status_code=500, detail=f'论文上传失败: {str(e)}')

from pydantic import BaseModel
from datetime import datetime
from typing import List

class EvaluateRequest(BaseModel):
    model_name: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    filename: str | None = None  # 添加文件名字段，用于指定要评价的论文文件

@router.get("/papers/debug")
async def debug_counts(paper_db: Session = Depends(get_paper_db)):
    """
    调试用：获取详细的数量信息
    """
    try:
        # 获取所有知识库文档
        knowledge_docs = db.query(KnowledgeBase).all()
        logger.info(f'知识库文档: {[{"id": k.id, "title": k.title} for k in knowledge_docs]}')

        # 获取所有论文
        papers = db.query(Paper).all()
        logger.info(f'论文: {[{"id": p.id, "title": p.title, "type": p.paper_type} for p in papers]}')

        return {
            "knowledge_docs": [
                {"id": k.id, "title": k.title, "file_path": k.file_path}
                for k in knowledge_docs
            ],
            "papers": [
                {"id": p.id, "title": p.title, "type": p.paper_type.value, "file_path": p.file_path}
                for p in papers
            ]
        }
    except Exception as e:
        logger.error(f'调试信息获取失败: {str(e)}')
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/papers/counts")
async def get_paper_counts(
    paper_db: Session = Depends(get_paper_db),
    knowledge_db: Session = Depends(get_knowledge_db)
):
    """
    获取各类型论文的数量
    """
    try:
        # 从 Knowledge 表获取知识库数量
        knowledge_count = knowledge_db.query(KnowledgeBase).count()
        logger.info(f'知识库数量: {knowledge_count}')

        # 从 Paper 表获取各类型论文数量
        paper_counts = paper_db.query(Paper.paper_type, func.count(Paper.id)).group_by(Paper.paper_type).all()
        paper_dict = {}
        for paper_type, count in paper_counts:
            if paper_type:
                paper_dict[paper_type.value] = count
        logger.info(f'论文数量: {paper_dict}')

        counts = {
            'undergraduate': paper_dict.get('undergraduate', 0),
            'master': paper_dict.get('master', 0),
            'phd': paper_dict.get('phd', 0),
            'knowledge_base': knowledge_count
        }
        return counts
    except HTTPException as e:
        logger.error(f'获取论文数量失败: {e.detail}')
        raise e
    except Exception as e:
        logger.error(f'获取论文数量失败: {str(e)}')
        logger.exception(e)  # 输出完整的堆栈信息
        raise HTTPException(
            status_code=500,
            detail=f'获取论文数量失败: {str(e)}'
        )

@router.post("/papers/upload-temp")
async def upload_temp_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_paper_db)
):
    """
    上传待评价的论文到evaluation目录
    """
    try:
        # 检查文件类型
        if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="只支持 PDF、DOC、DOCX 格式的文件"
            )

        # 检查文件大小
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="文件太大，请上传小于10MB的文件"
            )

        # 创建并保存文件到 evaluation 目录
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        evaluation_dir = os.path.join(base_dir, settings.PAPERS_DIR, 'evaluation')
        os.makedirs(evaluation_dir, exist_ok=True)
        file_path = os.path.join(evaluation_dir, file.filename)
        logger.info(f'开始保存文件: {file_path}')
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        logger.info(f'文件已保存到 evaluation 目录: {file_path}')
        return {
            "message": "文件已上传",
            "filename": file.filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'上传临时文件失败: {str(e)}')
        raise HTTPException(status_code=500, detail=f'上传失败: {str(e)}')

@router.post("/papers/evaluate/{paper_type}")
async def evaluate_paper(
    paper_type: str,
    request: EvaluateRequest,
    paper_db: Session = Depends(get_paper_db),
    evaluate_db: Session = Depends(get_evaluate_db),
    model_db: Session = Depends(get_model_db),
    knowledge_db: Session = Depends(get_knowledge_db)
):
    """
    评价论文
    """
    try:
        logger.info(f'开始评价{paper_type}论文')

        # 获取系统默认模型
        model_config = model_db.query(ModelConfig).first()
        if not model_config or not model_config.default_model:
            logger.error('未选择评价模型')
            raise HTTPException(
                status_code=400,
                detail='请先在模型管理页面选择并保存要使用的模型，然后再进行评价'
            )
            
        if not ollama_client.check_model(model_config.default_model):
            logger.error(f'模型 {model_config.default_model} 不可用')
            raise HTTPException(
                status_code=400,
                detail=f'模型 {model_config.default_model} 不可用'
            )
        
        # 检查知识库数量
        knowledge_count = knowledge_db.query(KnowledgeBase).count()
        logger.info(f'知识库数量: {knowledge_count}')
        if knowledge_count < 5:
            logger.error('知识库文档数量不足')
            raise HTTPException(
                status_code=400,
                detail='知识库中需要至少 5 篇文档'
            )

        # 准备评价文件目录
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        evaluation_dir = os.path.join(base_dir, settings.PAPERS_DIR, 'evaluation')
        os.makedirs(evaluation_dir, exist_ok=True)
        
        # 获取前端传递的文件名（如果有）
        filename = request.filename if hasattr(request, 'filename') and request.filename else None
        
        # 如果前端提供了文件名，使用指定的文件
        if filename:
            target_file = filename
            target_path = os.path.join(evaluation_dir, target_file)
            if not os.path.exists(target_path):
                raise HTTPException(
                    status_code=400,
                    detail=f'未找到指定的论文文件: {filename}'
                )
            logger.info(f'使用指定的文件进行评价: {target_file}')
        else:
            # 否则，在评价目录中查找最新的文件
            eval_files = os.listdir(evaluation_dir)
            if not eval_files:
                raise HTTPException(
                    status_code=400,
                    detail='未找到要评价的论文文件'
                )
            
            # 选择最新的文件
            eval_files.sort(key=lambda x: os.path.getmtime(os.path.join(evaluation_dir, x)), reverse=True)
            target_file = eval_files[0]
            target_path = os.path.join(evaluation_dir, target_file)
            logger.info(f'在评价目录找到最新文件: {target_file}')
        
        # 检查文件类型
        if not target_file.lower().endswith(('.pdf', '.doc', '.docx')):
            raise HTTPException(
                status_code=400,
                detail='不支持的文件类型'
            )
        
        # 读取文件内容
        try:
            paper_text = DocumentProcessor.process_document(target_path)
            if not paper_text:
                raise ValueError('无法提取文件内容')
        except Exception as e:
            logger.error(f'读取文件内容失败: {str(e)}')
            raise HTTPException(
                status_code=400,
                detail=f'读取文件内容失败: {str(e)}'
            )
        
        # 获取参考文献
        reference_texts = []
        try:
            # 从知识库中获取相关文献
            knowledge_items = knowledge_db.query(KnowledgeBase).all()
            reference_texts = []
            for item in knowledge_items:
                try:
                    text = DocumentProcessor.process_document(item.file_path)
                    if text:
                        reference_texts.append(text)
                except Exception as e:
                    logger.error(f'读取参考文献失败 (ID: {item.id}): {str(e)}')
                    continue
            logger.info(f'获取到 {len(reference_texts)} 篇参考文献')
        except Exception as e:
            logger.error(f'获取参考文献失败: {str(e)}')
            raise HTTPException(
                status_code=500,
                detail=f'获取参考文献失败: {str(e)}'
            )
        
        # 转换论文类型
        try:
            paper_type_enum = PaperType[paper_type]
        except KeyError:
            logger.error(f'无效的论文类型: {paper_type}')
            raise HTTPException(
                status_code=400,
                detail=f'无效的论文类型: {paper_type}'
            )
            
        # 获取同类型的历年论文作为比对材料
        historical_papers = []
        plagiarism_results = []
        try:
            # 查询同类型的论文
            same_type_papers = paper_db.query(Paper).filter(
                Paper.paper_type == paper_type_enum
            ).all()
            
            logger.info(f'找到 {len(same_type_papers)} 篇同类型历史论文')
            
            # 处理历史论文
            for hist_paper in same_type_papers:
                try:
                    # 跳过不存在的文件
                    if not os.path.exists(hist_paper.file_path):
                        logger.warning(f'历史论文文件不存在: {hist_paper.file_path}')
                        continue
                        
                    # 提取文本
                    hist_text = DocumentProcessor.process_document(hist_paper.file_path)
                    if not hist_text:
                        logger.warning(f'无法提取历史论文内容: {hist_paper.id}')
                        continue
                    
                    # 计算相似度
                    similarity = vector_store.calculate_similarity(paper_text, hist_text)
                    logger.info(f'论文相似度: 当前论文 vs {hist_paper.title} = {similarity}')
                    
                    # 添加到历史论文列表
                    historical_papers.append({
                        "id": hist_paper.id,
                        "title": hist_paper.title,
                        "text": hist_text,
                        "similarity": similarity
                    })
                    
                    # 检查是否可能抄袭
                    if similarity > 0.85:  # 设置相似度阈值
                        plagiarism_results.append({
                            "paper_id": hist_paper.id,
                            "title": hist_paper.title,
                            "similarity": similarity
                        })
                        logger.warning(f'检测到可能的抄袭: 当前论文 vs {hist_paper.title} = {similarity}')
                        
                except Exception as e:
                    logger.error(f'处理历史论文失败 (ID: {hist_paper.id}): {str(e)}')
                    continue
            
            # 按相似度排序
            historical_papers.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 取前5篇最相似的论文作为参考
            top_historical_papers = historical_papers[:5]
            logger.info(f'选择了 {len(top_historical_papers)} 篇最相似的历史论文作为参考')
            
        except Exception as e:
            logger.error(f'获取历史论文失败: {str(e)}')
            # 不中断评价流程，只记录错误
            top_historical_papers = []
        
        logger.info(f'最终获取到 {len(reference_texts)} 篇知识库参考文献和 {len(top_historical_papers)} 篇历史论文')

        # 创建论文记录
        paper = Paper(
            title=target_file,  # 暂时使用文件名作为标题
            file_path=target_path,
            paper_type=paper_type_enum,
            status='pending'
        )
        paper_db.add(paper)
        paper_db.commit()
        logger.info(f'论文记录已创建, ID: {paper.id}')

        # 评价论文
        try:
            evaluation = ollama_client.evaluate_paper(
                paper_text=paper_text,
                paper_type=paper_type_enum,
                reference_texts=reference_texts,
                historical_papers=top_historical_papers if 'top_historical_papers' in locals() else [],
                plagiarism_results=plagiarism_results if 'plagiarism_results' in locals() else [],
                model_name=model_config.default_model
            )
            
            # 验证评价结果
            score = evaluation.get('score')
            if not isinstance(score, (int, float)):
                raise ValueError(f'评价分数格式错误: {type(score)}')
            if not (65 <= float(score) <= 98):
                raise ValueError(f'评价分数超出范围: {score}')
                
            overall_comments = evaluation.get('overall_comments')
            if not isinstance(overall_comments, str) or len(overall_comments.strip()) < 50:
                raise ValueError('总体评价不能为空或过短')
            
            # 检查抄袭检测和历史比较结果
            plagiarism_check = evaluation.get('plagiarism_check', {})
            if not isinstance(plagiarism_check, dict):
                plagiarism_check = {
                    'is_plagiarized': False,
                    'comments': '未检测到抄袭问题'
                }
                
            historical_comparison = evaluation.get('historical_comparison', {})
            if not isinstance(historical_comparison, dict):
                historical_comparison = {
                    'improvement': 'unchanged',
                    'comments': '与历史论文相比无显著变化'
                }
            
            # 检查各部分评价
            sections = {
                'academic_evaluation': '学术评价',
                'ethical_evaluation': '伦理评价',
                'technical_analysis': '技术分析',
                'format_evaluation': '格式评价'
            }
            
            detailed_comments = []
            for section_name, section_title in sections.items():
                section = evaluation.get(section_name)
                if not isinstance(section, dict):
                    raise ValueError(f'{section_title}格式错误')
                
                section_comments = []
                for criterion, data in section.items():
                    if not isinstance(data, dict):
                        raise ValueError(f'{section_title}.{criterion}格式错误')
                    
                    subscore = data.get('score')
                    comments = data.get('comments')
                    
                    if not isinstance(subscore, (int, float)) or not (1 <= float(subscore) <= 10):
                        raise ValueError(f'{section_title}.{criterion}分数超出范围: {subscore}')
                    if not isinstance(comments, str) or not comments.strip():
                        raise ValueError(f'{section_title}.{criterion}评语不能为空')
                        
                    section_comments.append(f'{criterion}: {comments.strip()}')
                
                detailed_comments.append(f'\n{section_title}:\n' + '\n'.join(section_comments))
            
            # 添加抄袭检测和历史比较结果
            plagiarism_text = f"\n\n抄袭检测:\n检测结果: {'可能存在抄袭' if plagiarism_check.get('is_plagiarized') else '未发现抄袭问题'}\n评语: {plagiarism_check.get('comments', '')}"
            
            historical_text = f"\n\n与历史论文比较:\n水平变化: {historical_comparison.get('improvement', 'unchanged')}\n评语: {historical_comparison.get('comments', '')}"
            
            full_comments = overall_comments + '\n\n详细评价:\n' + '\n'.join(detailed_comments) + plagiarism_text + historical_text
            logger.info(f'评价结果: 分数={score}, 评语长度={len(full_comments)}')
            
            # 创建评价记录
            evaluation = Evaluation(
                paper_id=paper.id,
                score=float(score),
                comments=full_comments,
                model_name=model_config.default_model
            )
            evaluate_db.add(evaluation)
            evaluate_db.commit()
            logger.info(f'评价结果已保存到数据库, ID: {evaluation.id}')

            # 返回评价结果
            return {
                'id': evaluation.id,
                'paper_id': evaluation.paper_id,
                'paper_title': paper.title,
                'paper_type': paper_type,
                'score': evaluation.score,
                'comments': evaluation.comments,  # 直接使用完整的评价内容
                'model_name': evaluation.model_name,
                'plagiarism_check': {
                    'is_plagiarized': plagiarism_check.get('is_plagiarized', False),
                    'comments': plagiarism_check.get('comments', '')
                },
                'historical_comparison': {
                    'improvement': historical_comparison.get('improvement', 'unchanged'),
                    'comments': historical_comparison.get('comments', '')
                },
                'message': '论文评价完成'
            }

        except ValueError as e:
            logger.error(f'评价论文失败: {str(e)}')
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f'评价过程发生未知错误: {str(e)}')
            raise HTTPException(
                status_code=500,
                detail=f'评价失败: {str(e)}'
            )
    
    except HTTPException as e:
        # 直接向上抛出 HTTP 异常
        logger.error(f"论文评价失败: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"论文评价失败: {str(e)}")
        logger.exception(e)  # 输出完整的堆栈信息
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/papers/{paper_type}")
async def get_papers(paper_type: str = None, db: Session = Depends(get_paper_db)):
    """
    获取指定类型的论文列表
    """
    try:
        papers = db.query(Paper).filter(Paper.paper_type == paper_type).all()
        return {
            "papers": [
                {
                    "id": paper.id,
                    "title": paper.title,
                    "file_path": paper.file_path,
                    "created_at": paper.created_at,
                    "paper_type": paper.paper_type.value
                } for paper in papers
            ]
        }
    except Exception as e:
        logger.error(f"获取论文列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/papers/{paper_type}/{paper_id}")
async def delete_paper(
    paper_type: PaperType,
    paper_id: int,
    paper_db: Session = Depends(get_paper_db)
):
    """
    删除指定论文
    """
    try:
        # 查找论文
        paper = paper_db.query(Paper).filter(
            Paper.id == paper_id,
            Paper.paper_type == paper_type
        ).first()
        
        if not paper:
            raise HTTPException(
                status_code=404,
                detail=f"论文不存在或不属于{paper_type.value}类型"
            )
        
        # 删除文件
        try:
            if os.path.exists(paper.file_path):
                os.remove(paper.file_path)
                logger.info(f"成功删除文件: {paper.file_path}")
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"删除文件失败: {str(e)}"
            )
        
        # 删除数据库记录
        try:
            paper_db.delete(paper)
            paper_db.commit()
            logger.info(f"成功删除论文记录: {paper.id}")
        except Exception as e:
            paper_db.rollback()
            logger.error(f"删除数据库记录失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"删除数据库记录失败: {str(e)}"
            )
            
        # 删除向量存储中的数据
        try:
            if paper.vector:
                vector_store.delete_document(paper.vector)
                logger.info(f"成功删除向量数据: {paper.vector}")
        except Exception as e:
            logger.error(f"删除向量数据失败: {str(e)}")
            # 不抛出异常，因为这不影响主要功能
        
        return {"message": "论文删除成功"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除论文过程发生未知错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除论文失败: {str(e)}"
        )

        
        try:
            # 获取所有评价
            evaluations = evaluate_db.query(Evaluation).order_by(Evaluation.created_at.desc()).all()
            logger.info(f'找到 {len(evaluations)} 条评价记录')
            for eval in evaluations:
                logger.info(f'评价记录详情: id={eval.id}, paper_id={eval.paper_id}, score={eval.score}, model={eval.model_name}')
            
            if not evaluations:
                logger.info('没有找到评价记录')
                return {"evaluations": []}
            
            # 获取所有的论文ID
            paper_ids = [eval.paper_id for eval in evaluations]
            logger.info(f'需要查找的论文ID: {paper_ids}')
            
            # 获取评价对应的论文
            papers = {}
            if paper_ids:
                papers = {paper.id: paper for paper in paper_db.query(Paper).filter(Paper.id.in_(paper_ids)).all()}
            logger.info(f'找到 {len(papers)} 篇相关论文')
            for paper_id, paper in papers.items():
                logger.info(f'论文详情: id={paper_id}, title={paper.title}, type={paper.paper_type}')
            
            # 格式化返回数据
            for eval in evaluations:
                try:
                    paper = papers.get(eval.paper_id)
                    if not paper:
                        logger.warning(f'论文 {eval.paper_id} 不存在，跳过此评价记录')
                        continue
                        
                    # 确保所有字段都有默认值
                    try:
                        # 处理 paper_type
                        try:
                            paper_type = paper.paper_type.value if hasattr(paper.paper_type, 'value') else str(paper.paper_type)
                        except Exception as e:
                            logger.warning(f'获取 paper_type 失败: {str(e)}, 使用默认值 undergraduate')
                            paper_type = 'undergraduate'
                        logger.info(f'处理 paper_type: {paper_type}')
                        
                        # 处理 score
                        try:
                            score = float(eval.score) if eval.score is not None else 0.0
                        except Exception as e:
                            logger.warning(f'转换 score 失败: {str(e)}, 使用默认值 0.0')
                            score = 0.0
                        logger.info(f'处理 score: {score}')
                        
                        # 处理 timestamp
                        try:
                            timestamp = eval.created_at.isoformat() if eval.created_at else None
                        except Exception as e:
                            logger.warning(f'转换 timestamp 失败: {str(e)}, 使用默认值 None')
                            timestamp = None
                        logger.info(f'处理 timestamp: {timestamp}')
                        
                        evaluation_data = {
                            "id": eval.id,
                            "paperId": eval.paper_id,
                            "fileName": paper.title,
                            "title": paper.title,
                            "paperType": paper_type,
                            "modelName": eval.model_name if eval.model_name else "",
                            "score": score,
                            "comments": eval.comments if eval.comments else "",
                            "timestamp": timestamp
                        }
                    except Exception as e:
                        logger.error(f'格式化评价数据时出错: {str(e)}')
                        raise
                    
                    logger.debug(f'处理评价记录: {evaluation_data}')
                    result.append(evaluation_data)
                    
                except Exception as e:
                    logger.error(f'处理评价记录时出错: {str(e)}')
                    logger.exception(e)
                    continue
                    
            logger.info(f'返回数据: {result}')
            
            return {"evaluations": result}
        except Exception as e:
            logger.error(f'查询数据库时出错: {str(e)}')
            logger.exception(e)
            raise HTTPException(
                status_code=500,
                detail=f'查询数据库失败: {str(e)}'
            )
    except Exception as e:
        logger.error(f'获取评价历史失败: {str(e)}')
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f'获取评价历史失败: {str(e)}'
        )

@router.get("/papers/{paper_id}/evaluations")
async def get_paper_evaluations(
    paper_id: int,
    evaluate_db: Session = Depends(get_evaluate_db),
    paper_db: Session = Depends(get_paper_db)
):
    """
    获取指定论文的评价历史
    """
    try:
        # 获取论文信息
        paper = paper_db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail='论文不存在')

        # 获取评价历史
        evaluations = evaluate_db.query(Evaluation).filter(Evaluation.paper_id == paper_id).all()
        
        # 格式化评价历史
        evaluation_list = [{
            'id': eval.id,
            'paperId': eval.paper_id,
            'fileName': paper.file_name,
            'title': paper.title,
            'paperType': paper.paper_type.value,
            'modelName': eval.model_name,
            'score': eval.score,
            'comments': eval.comments,
            'timestamp': eval.created_at.isoformat() if eval.created_at else None
        } for eval in evaluations]
        
        return {"evaluations": evaluation_list}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f'获取论文评价历史失败: {str(e)}')
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f'获取论文评价历史失败: {str(e)}'
        )

@router.post("/evaluations/export")
async def export_evaluations(
    evaluations: List[int],
    evaluate_db: Session = Depends(get_evaluate_db),
    paper_db: Session = Depends(get_paper_db)
):
    """
    导出评价历史
    """
    try:
        # 获取指定的评价记录
        results = []
        for eval_id in evaluations:
            eval_record = evaluate_db.query(Evaluation).filter(Evaluation.id == eval_id).first()
            if eval_record:
                paper = paper_db.query(Paper).filter(Paper.id == eval_record.paper_id).first()
                if paper:
                    results.append({
                        'id': eval_record.id,
                        'paperId': eval_record.paper_id,
                        'fileName': paper.file_name,
                        'title': paper.title,
                        'paperType': paper.paper_type.value,
                        'modelName': eval_record.model_name,
                        'score': eval_record.score,
                        'comments': eval_record.comments,
                        'timestamp': eval_record.created_at.isoformat() if eval_record.created_at else None
                    })
        
        return {"evaluations": results}
    except Exception as e:
        logger.error(f'导出评价历史失败: {str(e)}')
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f'导出评价历史失败: {str(e)}'
        )

@router.delete("/evaluations")
async def clear_evaluations(
    paper_id: int,
    evaluate_db: Session = Depends(get_evaluate_db)
):
    """
    清空指定论文的评价历史
    """
    try:
        # 删除指定论文的所有评价记录
        evaluate_db.query(Evaluation).filter(Evaluation.paper_id == paper_id).delete()
        evaluate_db.commit()
        return {"message": "清空成功"}
    except Exception as e:
        evaluate_db.rollback()
        logger.error(f'清空评价历史失败: {str(e)}')
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=f'清空评价历史失败: {str(e)}'
        )
