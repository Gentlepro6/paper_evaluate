import PyPDF2
import docx
import pytesseract
from PIL import Image
import io
import logging
import os
from typing import List, Optional
import fitz  # PyMuPDF
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.core.config import OCR_LANGUAGES

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文档处理类，用于处理不同类型的文档"""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        从PDF文件中提取文本，使用多种方法确保最佳提取效果
        """
        try:
            text = ""
            doc = fitz.open(file_path)
            
            # 1. 首先尝试使用PyMuPDF直接提取文本
            for page in doc:
                page_text = page.get_text("text")
                if page_text.strip():
                    text += page_text + "\n"
            
            # 如果成功提取到文本，直接返回
            if text.strip():
                return text
                
            # 2. 如果没有文本，尝试使用pdfplumber
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # 如果pdfplumber成功提取到文本，返回结果
            if text.strip():
                return text
            
            # 3. 如果仍然没有文本，可能是扫描版PDF，使用OCR
            from pdf2image import convert_from_path
            import cv2
            import numpy as np
            
            # 将PDF转换为图片
            images = convert_from_path(file_path)
            
            for i, image in enumerate(images):
                # 转换为OpenCV格式
                img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # 图像预处理
                # 1. 转换为灰度图
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                # 2. 二值化
                _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                # 3. 降噪
                denoised = cv2.fastNlMeansDenoising(binary)
                
                # 对处理后的图像进行OCR
                for lang in OCR_LANGUAGES:
                    try:
                        page_text = pytesseract.image_to_string(
                            Image.fromarray(denoised),
                            lang=lang,
                            config='--psm 1 --oem 3'
                        )
                        if page_text.strip():
                            text += page_text + "\n"
                            break
                    except Exception as e:
                        logger.warning(f"OCR处理失败 (页面 {i+1}, 语言: {lang}): {str(e)}")
                        continue
            
            if not text.strip():
                logger.warning(f"无法从PDF提取文本: {file_path}")
                raise ValueError("无法从PDF提取文本，请确保PDF文件包含可识别的文本或清晰的扫描内容。")
                
            return text
            
        except Exception as e:
            logger.error(f"PDF处理错误: {str(e)}")
            raise

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """
        从DOCX文件中提取文本
        """
        try:
            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX处理错误: {str(e)}")
            raise

    @staticmethod
    def extract_text_from_doc(file_path: str) -> str:
        """
        从DOC文件中提取文本
        """
        try:
            # 先尝试直接用python-docx打开
            try:
                return DocumentProcessor.extract_text_from_docx(file_path)
            except Exception as docx_error:
                logger.debug(f"使用python-docx打开DOC文件失败: {str(docx_error)}")
            
            # 如果失败，则使用antiword
            import subprocess
            result = subprocess.run(['antiword', file_path], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            
            raise Exception("无法提取DOC文件的内容，请确保文件格式正确")
            
        except Exception as e:
            logger.error(f"DOC处理错误: {str(e)}")
            raise

    @classmethod
    def process_document(cls, file_path: str) -> str:
        """
        根据文件类型处理文档并提取文本
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return cls.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return cls.extract_text_from_docx(file_path)
        elif file_extension == '.doc':
            return cls.extract_text_from_doc(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_extension}")

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理提取的文本
        """
        # 移除多余的空白字符
        text = " ".join(text.split())
        # 移除特殊字符
        # 添加其他必要的清理步骤
        return text
