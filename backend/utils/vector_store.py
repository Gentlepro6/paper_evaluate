from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import logging
from typing import List, Dict, Any, Tuple
import os
from backend.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """向量存储和检索类"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化向量存储
        :param model_name: 使用的sentence-transformer模型名称
        """
        if self._initialized:
            return
            
        self.model = None
        self.index = None
        self.dimension = 384  # 默认维度
        self.document_map: Dict[int, Dict[str, Any]] = {}
        
        try:
            # 确保模型缓存目录存在
            cache_dir = os.path.abspath('./models')
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f'模型缓存目录：{cache_dir}')
            
            # 检查缓存目录中是否已有模型文件
            model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
            model_files_exist = False
            model_dir = os.path.join(cache_dir, model_name)
            
            if os.path.exists(model_dir):
                logger.info(f'检测到模型目录存在: {model_dir}')
                # 检查模型文件是否完整
                required_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json']
                files_in_dir = os.listdir(model_dir) if os.path.isdir(model_dir) else []
                logger.info(f'模型目录内容: {files_in_dir}')
                
                # 检查关键模型文件是否存在
                if any(f for f in files_in_dir if f.endswith('.bin')):
                    model_files_exist = True
                    logger.info('检测到模型文件已存在')
            
            # 尝试加载模型，如果不存在则下载
            try:
                if model_files_exist:
                    logger.info(f'使用本地缓存的模型: {model_name}')
                else:
                    logger.info(f'模型文件不存在，将从网络下载: {model_name}')
                
                # 加载或下载模型
                logger.info(f'开始加载模型: {model_name}')
                self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
                logger.info('模型加载成功')
            except Exception as e:
                logger.error(f'模型加载失败：{str(e)}')
                logger.warning('将以有限功能模式运行，知识库搜索功能将不可用')
            
            # 如果模型加载成功，获取实际维度
            if self.model:
                test_text = "测试文本"
                test_vector = self.model.encode([test_text])[0]
                self.dimension = len(test_vector)
                logger.info(f'模型输出维度：{self.dimension}')
            
            # 初始化FAISS索引
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info('向量存储初始化完成')
            
            # 标记初始化完成
            self._initialized = True
            
        except Exception as e:
            logger.error(f'初始化VectorStore时发生错误：{str(e)}')
            logger.warning('将以有限功能模式运行，知识库搜索功能将不可用')

    def add_document(self, text: str, metadata: Dict[str, Any]) -> int:
        """
        添加文档到向量存储
        :param text: 文档文本
        :param metadata: 文档元数据
        :return: 文档ID
        """
        try:
            if not self.model or not self.index:
                raise RuntimeError("向量存储未正确初始化，无法添加文档")
                
            logger.debug(f"开始生成文档向量，文本长度: {len(text)}")
            
            # 生成文档向量
            vector = self.model.encode([text])[0]
            vector = np.array(vector, dtype=np.float32)  # 确保数据类型正确
            
            if len(vector) != self.dimension:
                raise ValueError(f"向量维度不匹配，期望: {self.dimension}, 实际: {len(vector)}")
            
            # 添加到FAISS索引
            vector = vector.reshape(1, -1)
            doc_id = len(self.document_map)
            self.index.add(vector)
            
            # 存储文档元数据
            self.document_map[doc_id] = {
                "metadata": metadata,
                "vector": vector.reshape(-1).tolist()
            }
            
            logger.info(f"文档向量生成成功，ID: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {str(e)}")
            raise

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        搜索最相似的文档
        :param query: 查询文本
        :param top_k: 返回结果数量
        :return: [(doc_id, distance, metadata), ...]
        """
        try:
            if not self.model or not self.index:
                raise RuntimeError("向量存储未正确初始化，无法执行搜索")
                
            # 生成查询向量
            query_vector = self.model.encode([query])[0]
            query_vector = query_vector.reshape(1, -1)
            
            # 搜索最近邻
            distances, indices = self.index.search(query_vector, top_k)
            
            # 整理结果
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx != -1:  # FAISS返回-1表示无效结果
                    doc_data = self.document_map.get(int(idx))
                    if doc_data:
                        results.append((int(idx), float(distance), doc_data["metadata"]))
            
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            raise

    def save(self, directory: str):
        """
        保存向量索引和文档映射
        :param directory: 保存目录
        """
        try:
            os.makedirs(directory, exist_ok=True)
            
            # 保存FAISS索引
            index_path = os.path.join(directory, "index.faiss")
            faiss.write_index(self.index, index_path)
            
            # 保存文档映射
            map_path = os.path.join(directory, "document_map.json")
            with open(map_path, 'w', encoding='utf-8') as f:
                # 将numpy数组转换为列表以便JSON序列化
                serializable_map = {}
                for k, v in self.document_map.items():
                    serializable_map[str(k)] = {
                        "metadata": v["metadata"],
                        "vector": v["vector"]
                    }
                json.dump(serializable_map, f, ensure_ascii=False, indent=2)
            
            logger.info(f"向量存储已保存到: {directory}")
        except Exception as e:
            logger.error(f"保存向量存储失败: {str(e)}")
            raise

    @classmethod
    def load(cls, directory: str) -> 'VectorStore':
        """
        加载向量索引和文档映射
        :param directory: 加载目录
        :return: VectorStore实例
        """
        try:
            instance = cls()
            
            # 加载FAISS索引
            index_path = os.path.join(directory, "index.faiss")
            instance.index = faiss.read_index(index_path)
            
            # 加载文档映射
            map_path = os.path.join(directory, "document_map.json")
            with open(map_path, 'r', encoding='utf-8') as f:
                serialized_map = json.load(f)
                instance.document_map = {
                    int(k): {
                        "metadata": v["metadata"],
                        "vector": v["vector"]
                    }
                    for k, v in serialized_map.items()
                }
            
            logger.info(f"向量存储已从 {directory} 加载")
            return instance
        except Exception as e:
            logger.error(f"加载向量存储失败: {str(e)}")
            raise
            
    def encode_text(self, text: str) -> np.ndarray:
        """
        将文本编码为向量
        :param text: 要编码的文本
        :return: 文本向量
        """
        try:
            if not self.model:
                raise RuntimeError("向量模型未初始化，无法编码文本")
                
            # 生成文本向量
            vector = self.model.encode([text])[0]
            vector = np.array(vector, dtype=np.float32)  # 确保数据类型正确
            
            if len(vector) != self.dimension:
                raise ValueError(f"向量维度不匹配，期望: {self.dimension}, 实际: {len(vector)}")
                
            return vector
        except Exception as e:
            logger.error(f"文本编码失败: {str(e)}")
            raise
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本之间的相似度
        :param text1: 第一个文本
        :param text2: 第二个文本
        :return: 相似度分数 (0-1 之间的浮点数，1表示完全相同)
        """
        try:
            if not self.model:
                raise RuntimeError("向量模型未初始化，无法计算相似度")
            
            # 编码两个文本
            vector1 = self.encode_text(text1)
            vector2 = self.encode_text(text2)
            
            # 计算余弦相似度
            # 余弦相似度 = 向量点积 / (向量1范数 * 向量2范数)
            dot_product = np.dot(vector1, vector2)
            norm1 = np.linalg.norm(vector1)
            norm2 = np.linalg.norm(vector2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            
            # 确保结果在0-1之间
            similarity = max(0.0, min(1.0, similarity))
            
            logger.debug(f"文本相似度计算结果: {similarity}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算文本相似度失败: {str(e)}")
            raise
