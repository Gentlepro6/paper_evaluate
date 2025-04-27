from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.utils.ollama_client import OllamaClient
from backend.core.config import settings
from backend.database import get_db as get_model_db, ModelConfig
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
ollama_client = OllamaClient()

class ModelConfigUpdate(BaseModel):
    server_url: str | None = None
    default_model: str | None = None
    temperature: float = 0.3
    max_tokens: int = 2000
    
    class Config:
        json_schema_extra = {
            "example": {
                "server_url": "http://localhost:11434",
                "default_model": "llama2",
                "temperature": 0.3,
                "max_tokens": 2000
            }
        }

@router.get("/models")
async def list_models(server_url: str = None):
    """
    获取可用的模型列表
    """
    try:
        # 如果提供了服务器URL，尝试连接新服务器
        if server_url:
            client = OllamaClient(base_url=server_url)
            logger.info(f'尝试连接新服务器: {server_url}')
            models = client.list_models()
            logger.info(f'从新服务器获取的模型列表: {models}')
            if not models.get('models'):
                raise ValueError('无法从服务器获取模型列表')
            return models
        
        # 使用默认服务器
        logger.info(f'从默认服务器获取模型列表: {ollama_client.base_url}')
        models = ollama_client.list_models()
        logger.info(f'从默认服务器获取的模型列表: {models}')
        return models
        
    except Exception as e:
        logger.error(f'获取模型列表失败: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'获取模型列表失败: {str(e)}'
        )

@router.get("/models/{model_name}/check")
async def check_model(model_name: str):
    """
    检查模型是否已安装
    """
    try:
        exists = ollama_client.check_model(model_name)
        return {"exists": exists}
    except Exception as e:
        logger.error(f'检查模型状态失败: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'检查模型状态失败: {str(e)}'
        )

@router.post("/models/test")
async def test_model(request: dict):
    """
    测试模型是否正常工作
    """
    try:
        model_name = request.get('model_name', settings.DEFAULT_MODEL)
        server_url = request.get('server_url')
        
        # 创建客户端
        client = OllamaClient(base_url=server_url)
        
        # 首先检查模型是否存在
        if not client.check_model(model_name):
            raise ValueError(f'模型 {model_name} 不存在')
        
        # 测试模型
        logger.info(f'开始测试模型: {model_name}, 服务器: {client.base_url}')
        response = client.generate(
            prompt='这是一个测试。请回复：模型工作正常。',
            model_name=model_name,
            max_tokens=50
        )
        
        return {
            "status": "success",
            "model": model_name,
            "response": response
        }
        
    except ValueError as e:
        logger.error(f'模型测试失败: {str(e)}')
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f'模型测试失败: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'模型测试失败: {str(e)}'
        )

@router.get("/models/config")
async def get_model_config(db: Session = Depends(get_model_db)):
    """
    获取当前模型配置
    """
    try:
        model_config = db.query(ModelConfig).first()
        
        # 如果没有配置，返回默认配置
        if not model_config:
            default_config = ModelConfig.get_default_config()
            return {
                "status": "success",
                "is_default": True,
                "config": default_config
            }
        
        return {
            "status": "success",
            "is_default": False,
            "config": {
                "server_url": model_config.server_url,
                "default_model": model_config.default_model,
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_tokens
            }
        }
        
    except Exception as e:
        logger.error(f'获取配置失败: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'获取配置失败: {str(e)}'
        )

@router.post("/models/config")
async def update_model_config(
    config: ModelConfigUpdate,
    db: Session = Depends(get_model_db)
):
    """
    更新模型配置
    """
    try:
        # 验证新服务器和模型
        if config.server_url is not None:
            try:
                client = OllamaClient(base_url=config.server_url)
                if config.default_model and not client.check_model(config.default_model):
                    raise ValueError(f'模型 {config.default_model} 在新服务器上不可用')
            except Exception as e:
                raise ValueError(f'无法连接到服务器 {config.server_url}: {str(e)}')
        
        # 验证参数
        if not (0 <= config.temperature <= 1):
            raise ValueError('温度参数必须在 0 和 1 之间')
        if config.max_tokens < 1:
            raise ValueError('最大token数必须大于 0')
        
        # 更新或创建配置
        try:
            model_config = db.query(ModelConfig).first()
            logger.info(f'当前配置: {model_config}')
        except Exception as e:
            logger.error(f'查询配置失败: {str(e)}')
            raise ValueError(f'查询配置失败: {str(e)}')

        if not model_config:
            logger.info('创建新配置')
            model_config = ModelConfig()

        # 记录要更新的字段
        logger.info(f'更新配置: server_url={config.server_url}, default_model={config.default_model}, '
                  f'temperature={config.temperature}, max_tokens={config.max_tokens}')
            
        # 只更新非空的字段
        if config.server_url is not None:
            model_config.server_url = config.server_url
        if config.default_model is not None:
            model_config.default_model = config.default_model
        if config.temperature is not None:
            model_config.temperature = config.temperature
        if config.max_tokens is not None:
            model_config.max_tokens = config.max_tokens
        
        try:
            logger.info('开始保存配置...')
            db.add(model_config)
            db.commit()
            db.refresh(model_config)
            logger.info('模型配置已成功更新')
            
            return {
                "status": "success",
                "message": "配置更新成功",
                "config": {
                    "server_url": model_config.server_url,
                    "default_model": model_config.default_model,
                    "temperature": model_config.temperature,
                    "max_tokens": model_config.max_tokens
                }
            }
        except Exception as e:
            logger.error(f'保存配置失败: {str(e)}')
            db.rollback()
            raise ValueError(f'保存配置失败: {str(e)}')
    
    except ValueError as e:
        logger.error(f'配置验证失败: {str(e)}')
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f'更新配置失败: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'更新配置失败: {str(e)}'
        )
