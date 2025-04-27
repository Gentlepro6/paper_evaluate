import requests
import json
import logging
import re
from typing import Dict, Any, Optional
from fastapi import HTTPException
from backend.core.config import settings
from sqlalchemy.orm import Session
from backend.database import get_db as get_model_db, ModelConfig

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama API客户端"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        初始化Ollama客户端
        :param base_url: Ollama API的基础URL
        """
        self._base_url = base_url
        self._config = None
    
    def _load_config(self) -> None:
        """从数据库加载配置"""
        if self._base_url is not None:
            return

        try:
            db = next(get_model_db())
            config = db.query(ModelConfig).first()
            if config:
                self._config = config
                logger.info(f'从数据库加载配置: {config}')
        except Exception as e:
            logger.error(f'加载配置失败: {str(e)}')
            self._config = None
    
    @property
    def base_url(self) -> str:
        """获取服务器URL"""
        if self._base_url is not None:
            return self._base_url
        
        self._load_config()
        if self._config and self._config.server_url:
            return self._config.server_url
        return settings.OLLAMA_BASE_URL
    
    @property
    def default_model(self) -> str:
        """获取默认模型"""
        self._load_config()
        if self._config and self._config.default_model:
            return self._config.default_model
        
        if settings.DEFAULT_MODEL:
            return settings.DEFAULT_MODEL
            
        raise ValueError('未配置默认模型，请在模型管理页面配置')
    
    @property
    def temperature(self) -> float:
        """获取温度参数"""
        if self._base_url is not None:
            return 0.3
        
        self._load_config()
        if self._config:
            return self._config.temperature
        return 0.3
    
    @property
    def max_tokens(self) -> int:
        """获取最大token数"""
        if self._base_url is not None:
            return 2000
        
        self._load_config()
        if self._config:
            return self._config.max_tokens
        return 2000
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Any:
        """
        发送请求到 Ollama API
        """
        # 如果端点已经包含 api，则不再添加
        if not endpoint.startswith('api/'):
            endpoint = f'api/{endpoint}'
            
        url = f"{self.base_url}/{endpoint}"
        timeout = 30  # 设置 30 秒超时
        
        try:
            logger.info(f'发送 {method} 请求到 {url}')
            if data:
                logger.info(f'请求数据: {data}')
                
            if method == "GET":
                response = requests.get(url, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=120)  # 增加超时时间到120秒
            else:
                raise ValueError(f"不支持的请求方法: {method}")
                
            if response.status_code != 200:
                error_msg = f'服务器响应错误 {response.status_code}: {response.text}'
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            try:
                result = response.json()
                logger.info(f'响应数据: {result}')
                return result
            except json.JSONDecodeError as e:
                error_msg = f'响应中没有找到JSON格式的内容\n响应状态码: {response.status_code}\n响应内容: {response.text}\n错误信息: {str(e)}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if isinstance(result, dict) and 'error' in result:
                error_msg = f'服务器错误: {result["error"]}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            if not result:
                error_msg = '服务器返回空响应'
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            return result
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f'连接失败: {str(e)}')
            raise ValueError(f'无法连接到Ollama服务器，请确保服务器地址正确且服务器已启动')
        except requests.exceptions.Timeout as e:
            logger.error(f'请求超时: {str(e)}')
            raise ValueError('请求超时，请检查服务器状态')
        except requests.exceptions.RequestException as e:
            logger.error(f'请求失败: {str(e)}')
            raise ValueError(f'请求失败: {str(e)}')
        except json.JSONDecodeError as e:
            logger.error(f'解析响应失败: {str(e)}')
            raise HTTPException(
                status_code=500,
                detail=f'解析响应失败: {str(e)}'
            )
    
    def list_models(self) -> Dict[str, Any]:
        """
        获取已安装的Ollama模型列表
        返回格式：{"models": [{"name": "模型名称", "size": 模型大小}]}
        """
        try:
            response = self._make_request('tags')
            logger.info(f'从服务器获取到的原始响应: {response}')
            
            if not response:
                logger.error('服务器返回空响应')
                return {"models": []}
            
            if not isinstance(response, dict):
                logger.error(f'响应不是字典格式: {type(response)}')
                return {"models": []}
            
            # 将 Ollama API 的响应格式转换为我们需要的格式
            models = [{
                'name': model.get('name', ''),  # 显示名称
                'model': model.get('name', ''),  # 模型标识符
                'size': model.get('size', 0)
            } for model in response.get('models', [])]
            
            logger.info(f'处理后的模型列表: {models}')
            return {'models': models}
            
        except Exception as e:
            logger.error(f'获取模型列表失败: {str(e)}')
            return {"models": []}
    
    def check_model(self, model_name: str) -> bool:
        """
        检查模型是否已安装
        """
        try:
            logger.info(f'检查模型是否可用: {model_name}')
            models = self.list_models()
            
            if not models or 'models' not in models:
                logger.error('获取模型列表失败')
                return False
                
            available = any(model['model'] == model_name for model in models.get('models', []))
            if not available:
                logger.warning(f'模型 {model_name} 不可用')
            else:
                logger.info(f'模型 {model_name} 可用')
            return available
            
        except Exception as e:
            logger.error(f'检查模型时发生错误: {str(e)}')
            return False
    
    def generate(self, 
                prompt: str, 
                model_name: str | None = None,
                system_prompt: Optional[str] = None,
                temperature: float | None = None,
                max_tokens: int | None = None) -> str:
        """
        生成文本响应
        :param prompt: 提示文本
        :param model_name: 模型名称
        :param system_prompt: 系统提示
        :param temperature: 温度参数
        :param max_tokens: 最大生成token数
        :return: 生成的文本
        """
        try:
            # 参数验证和默认值设置
            if not prompt:
                raise ValueError("提示文本不能为空")
            
            model_name = model_name or self.default_model
            if not model_name:
                raise ValueError("未指定模型名称")
                
            temperature = temperature if temperature is not None else self.temperature
            max_tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # 检查模型是否存在
            if not self.check_model(model_name):
                raise ValueError(f"模型 {model_name} 不存在或无法访问")
            
            # 准备请求数据
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            if temperature is not None:
                data["temperature"] = temperature
                
            if max_tokens is not None:
                data["num_predict"] = max_tokens
            
            # 发送请求
            logger.info(f'使用模型 {model_name} 生成文本')
            logger.debug(f'请求数据: {data}')
            
            try:
                response = self._make_request('generate', method="POST", data=data)
                logger.debug(f'原始响应: {response}')
            except Exception as e:
                logger.error(f'请求失败: {str(e)}')
                raise ValueError(f'无法连接到 Ollama 服务器: {str(e)}')
            
            if not response:
                raise ValueError('服务器返回空响应')
                
            if isinstance(response, dict):
                if 'error' in response:
                    raise ValueError(f'服务器错误: {response["error"]}')
                if 'response' in response:
                    return response['response']
                    
            # 如果响应不是字典或没有response字段，返回原始响应
            return str(response)
            
        except ValueError as e:
            logger.error(f'生成文本失败: {str(e)}')
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f'生成文本失败: {str(e)}')
            raise ValueError(f'生成文本失败: {str(e)}')
    
    def evaluate_paper(self, 
                      paper_text: str, 
                      paper_type: str,
                      reference_texts: list[str],
                      historical_papers: list[dict] = None,
                      plagiarism_results: list[dict] = None,
                      model_name: str | None = None) -> Dict[str, Any]:
        """
        评价论文
        :param paper_text: 论文文本
        :param paper_type: 论文类型（本科/硕士/博士）
        :param reference_texts: 参考文献列表
        :param model_name: 使用的模型名称
        :return: 评价结果，包含分数和评语
        """
        # 验证参数
        if not paper_text:
            raise ValueError('论文文本不能为空')
        if not paper_type:
            raise ValueError('论文类型不能为空')
        
        # 检查模型
        model_name = model_name or self.default_model
        if not model_name:
            raise ValueError('未选择模型')
        
        logger.info(f'使用模型: {model_name}')
        
        if not self.check_model(model_name):
            raise ValueError(f'模型 {model_name} 不可用')
        
        # 获取论文类型名称
        paper_type_map = {
            'undergraduate': '本科',
            'master': '硕士',
            'phd': '博士'
        }
        paper_type_str = paper_type_map.get(paper_type.value if hasattr(paper_type, 'value') else paper_type, '未知')
        
        # 准备历史论文信息
        historical_papers = historical_papers or []
        plagiarism_results = plagiarism_results or []
        
        # 处理历史论文数据
        historical_papers_text = ""
        if historical_papers:
            historical_papers_text = "\n\n历年同类型论文（按相似度排序）：\n"
            for i, paper in enumerate(historical_papers[:3]):  # 只取前3篇最相似的
                historical_papers_text += f"\n论文 {i+1}:\n"
                historical_papers_text += f"标题: {paper['title']}\n"
                historical_papers_text += f"相似度: {paper['similarity']:.4f}\n"
                # 只取前1000个字符作为样本
                text_sample = paper['text'][:1000] + "..." if len(paper['text']) > 1000 else paper['text']
                historical_papers_text += f"内容摘要: {text_sample}\n"
        
        # 处理抄袭检测结果
        plagiarism_text = ""
        if plagiarism_results:
            plagiarism_text = "\n\n注意：检测到以下可能的抄袭情况：\n"
            for i, result in enumerate(plagiarism_results):
                plagiarism_text += f"\n抄袭可能性 {i+1}:\n"
                plagiarism_text += f"论文标题: {result['title']}\n"
                plagiarism_text += f"相似度: {result['similarity']:.4f}\n"
        
        # 准备提示文本
        prompt = f"""
        请仔细阅读并评价以下{paper_type_str}论文。

        论文内容：
        ```
        {paper_text}
        ```

        参考文献：
        ```
        {chr(10).join(reference_texts) if reference_texts else '无参考文献'}
        ```
        {historical_papers_text}
        {plagiarism_text}

        请基于以上内容进行评价。您必须使用严格的JSON格式输出评价结果，不要添加任何其他内容。
        以下是要求的输出格式：
        {{
            "score": 总分(65-98),
            "academic_evaluation": {{
                "significance": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }},
                "innovation": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }},
                "methodology": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }},
                "results": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }}
            }},
            "ethical_evaluation": {{
                "academic_integrity": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }},
                "research_ethics": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }}
            }},
            "technical_analysis": {{
                "literature_review": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }},
                "data_analysis": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }},
                "contribution": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }}
            }},
            "format_evaluation": {{
                "writing": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }},
                "structure": {{
                    "score": 分数(1-10),
                    "comments": "评语"
                }}
            }},
            "plagiarism_check": {{
                "is_plagiarized": 是否有抄袭嫌疑(true/false),
                "comments": "关于抄袭检测的评语"
            }},
            "historical_comparison": {{
                "improvement": "与历史论文相比的水平差异(improved/unchanged/declined)",
                "comments": "与历年论文相比的学术水平评价"
            }},
            "overall_comments": "详细的总体评价评语，不少于100个字"
        }}
        
        请严格按照上述格式输出，不要添加其他字段或修改字段名称。
        每个子项必须包含对应的字段。
        总体评价评语必须详细全面，不少于100个字，包含论文的主要优缺点、创新性、学术价值、改进建议等。
        
        特别注意：
        1. 请评估论文是否存在抄袭问题，并在plagiarism_check字段中给出评价
        2. 请将当前论文与历年同类型论文进行比较，评估学术水平是否有所提高
        """
        
        

        # 设置系统提示
        system_prompt = f"""
        You are a professional thesis evaluation expert. Your task is to carefully read the thesis and provide an objective and fair evaluation.
        You must use strict JSON format output, exactly as follows:
        {{
            "score": number(65-98),
            "plagiarism_check": {{
                "is_plagiarized": boolean,
                "comments": "string"
            }},
            "historical_comparison": {{
                "improvement": "string(improved/unchanged/declined)",
                "comments": "string"
            }},
            "academic_evaluation": {{
                "significance": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }},
                "innovation": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }},
                "methodology": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }},
                "results": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }}
            }},
            "ethical_evaluation": {{
                "academic_integrity": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }},
                "research_ethics": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }}
            }},
            "technical_analysis": {{
                "literature_review": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }},
                "data_analysis": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }},
                "contribution": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }}
            }},
            "format_evaluation": {{
                "writing": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }},
                "structure": {{
                    "score": number(1-10),
                    "comments": "comments in Chinese"
                }}
            }},
            "overall_comments": "detailed overall evaluation comments in Chinese"
        }}

        Paper Content:
        {paper_text[:2000]}

        References:
        {' '.join(ref[:500] for ref in reference_texts[:3]) if reference_texts else 'No references'}
        """

        try:
            # 生成评价
            response = self.generate(
                prompt=prompt,
                model_name=model_name,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            logger.info('成功获取模型响应: ' + response)
            
            # 解析和验证响应
            try:
                # 尝试查找JSON内容
                start = response.find('{')
                end = response.rfind('}')
                logger.info(f'原始响应: {response}')
                logger.info(f'JSON开始位置: {start}, 结束位置: {end}')
                
                if start >= 0 and end >= 0:
                    json_str = response[start:end+1]
                    logger.info(f'提取的JSON字符串: {json_str}')
                    result = json.loads(json_str)
                    logger.info(f'解析后的JSON对象: {result}')
                else:
                    raise ValueError('响应中未找到JSON内容')
                
                # 验证基本结构
                required_fields = [
                    'score',
                    'academic_evaluation',
                    'ethical_evaluation',
                    'technical_analysis',
                    'format_evaluation',
                    'overall_comments'
                ]
                
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f'缺少必需字段: {field}')
                
                # 验证分数范围
                score = result.get('score')
                if not isinstance(score, (int, float)) or not (65 <= score <= 98):
                    raise ValueError(f'总分 {score} 不在有效范围内(65-98)')
                
                # 验证各部分评价
                sections = {
                    'academic_evaluation': ['significance', 'innovation', 'methodology', 'results'],
                    'ethical_evaluation': ['academic_integrity', 'research_ethics'],
                    'technical_analysis': ['literature_review', 'data_analysis', 'contribution'],
                    'format_evaluation': ['writing', 'structure']
                }
                
                for section, criteria in sections.items():
                    if not isinstance(result[section], dict):
                        raise ValueError(f'{section} 不是一个有效的对象')
                    
                    for criterion in criteria:
                        if criterion not in result[section]:
                            raise ValueError(f'{section} 缺少 {criterion} 字段')
                        
                        item = result[section][criterion]
                        if not isinstance(item, dict):
                            raise ValueError(f'{section}.{criterion} 不是一个有效的对象')
                        
                        if 'score' not in item or 'comments' not in item:
                            raise ValueError(f'{section}.{criterion} 缺少 score 或 comments 字段')
                        
                        # 验证分数
                        subscore = item['score']
                        if not isinstance(subscore, (int, float)) or not (1 <= subscore <= 10):
                            raise ValueError(f'{section}.{criterion} 的分数 {subscore} 不在有效范围内(1-10)')
                        
                        # 验证评语
                        comments = item['comments']
                        if not isinstance(comments, str) or not comments.strip():
                            raise ValueError(f'{section}.{criterion} 评语不能为空')
                
                # 验证总体评价
                if not isinstance(result['overall_comments'], str) or not result['overall_comments'].strip():
                    raise ValueError('总体评价不能为空')
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f'JSON解析失败: {str(e)}')
                logger.error(f'原始响应: {response}')
                raise ValueError('响应格式无效') from e
                
            except ValueError as e:
                logger.error(f'响应格式不正确: {str(e)}')
                raise
                
        except Exception as e:
            logger.error(f'论文评价失败: {str(e)}')
            raise


    def _is_valid_evaluation(self, result: Any) -> bool:
        """
        检查评价结果是否有效
        :param result: 要检查的评价结果
        :return: 如果结果有效返回 True，否则返回 False
        """
        if not isinstance(result, dict):
            return False
            
        # 检查必要字段
        required_fields = [
            'score',
            'academic_evaluation',
            'ethical_evaluation',
            'technical_analysis',
            'format_evaluation',
            'overall_comments'
        ]
        
        for field in required_fields:
            if field not in result:
                logger.error(f'缺少必要字段: {field}')
                return False
        
        # 检查总分是否在有效范围内
        try:
            score = float(result['score'])
            if not (65 <= score <= 98):
                logger.error(f'总分超出范围: {score}')
                return False
        except (ValueError, TypeError):
            logger.error('总分格式错误')
            return False
            
        # 检查各组成部分
        evaluation_sections = {
            'academic_evaluation': ['significance', 'innovation', 'methodology', 'results'],
            'ethical_evaluation': ['academic_integrity', 'research_ethics'],
            'technical_analysis': ['literature_review', 'data_analysis', 'contribution'],
            'format_evaluation': ['writing', 'structure']
        }
        
        for section, criteria in evaluation_sections.items():
            if not isinstance(result[section], dict):
                logger.error(f'{section} 不是字典类型')
                return False
                
            for criterion in criteria:
                if criterion not in result[section]:
                    logger.error(f'{section} 缺少 {criterion}')
                    return False
                    
                criterion_data = result[section][criterion]
                if not isinstance(criterion_data, dict):
                    logger.error(f'{section}.{criterion} 不是字典类型')
                    return False
                    
                # 检查分数和评语
                if 'score' not in criterion_data or 'comments' not in criterion_data:
                    logger.error(f'{section}.{criterion} 缺少分数或评语')
                    return False
                    
                try:
                    subscore = float(criterion_data['score'])
                    if not (1 <= subscore <= 10):
                        logger.error(f'{section}.{criterion} 分数超出范围: {subscore}')
                        return False
                except (ValueError, TypeError):
                    logger.error(f'{section}.{criterion} 分数格式错误')
                    return False
                    
                if not isinstance(criterion_data['comments'], str) or not criterion_data['comments'].strip():
                    logger.error(f'{section}.{criterion} 评语为空')
                    return False
        
        # 检查总体评价
        if not isinstance(result['overall_comments'], str) or not result['overall_comments'].strip():
            logger.error('总体评价为空')
            return False
            
        return True
