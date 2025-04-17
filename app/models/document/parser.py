import os
import shutil
import hashlib
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import re
from typing import List
import logging

from docx import Document
from datetime import datetime
import json
from app.models.document.models import DocumentImage, DocumentChunk, DocumentItem
from app.models.document.utils import get_outline_level, extract_image_from_run, parse_document_content
from app.utils.maas_client import vision_completion

logger = logging.getLogger(__name__)

class DocumentParser:
    """文档解析器，用于将文档转换为markdown格式"""
    
    def __init__(self, 
                 source_dir: str = 'data/upload', 
                 markdown_dir: str = 'data/document/markdown',
                 images_dir: str = 'data/document/images',
                 chunks_dir: str = 'data/document/chunks',
                 extracted_dir: str = 'data/document/extracted',
                 cleanup: bool = True,
                 collector: str = '系统',
                 project: str = '默认项目'):
        self.source_dir = Path(source_dir)
        self.markdown_dir = Path(markdown_dir)
        self.images_dir = Path(images_dir)
        self.chunks_dir = Path(chunks_dir)
        self.extracted_dir = Path(extracted_dir)
        self.cleanup = cleanup
        self.image_counter = 0
        self.collector = collector
        self.project = project

    def parse_docx(self, file_path: Path) -> DocumentItem:
        """解析docx文件为结构化的DocumentItem格式
        
        Args:
            file_path: docx文件路径
            output_dir: 保存提取图片的目录
            
        Returns:
            DocumentItem: 包含内容、分块和图片的结构化文档数据
        """
        doc = Document(file_path)
        content = ""
        images = []
        image_counter = 0

        # 处理每个段落
        for paragraph in doc.paragraphs:
            # 确定段落大纲级别（如果有）
            outline_level = get_outline_level(paragraph)
            if outline_level is not None:
                # 根据大纲级别生成Markdown标题
                content += "#" * outline_level + " " + paragraph.text.strip() + "\n\n"
                continue
            
            # 添加普通段落文本
            text = paragraph.text.strip()
            if text:
                content += text + "\n\n"
            
            for run in paragraph.runs:
                if run.element.xpath('.//w:drawing'):
                    # 获取图片唯一标识
                    image_info = extract_image_from_run(doc = doc, run = run, image_counter = image_counter, output_dir = self.images_dir / file_path.stem)
                    image_counter += 1
                    if image_info:
                        # 调用VLM生成图片描述
                        image_description = vision_completion(
                            image_info['url'], 
                            prompt="当前正在处理网络安全相关文档，需要从图片中提取关键信息和描述内容"
                        )
                        # 替换描述中的标题符号为制表符
                        image_description = image_description.replace('#', '\t')
                        
                        # 更新图片信息包含描述
                        image_info["description"] = image_description
                        image_info["collector"] = self.collector
                        image_info["project"] = self.project
                        image_info["evidence_type"] = "image"
                        images.append(DocumentImage(**image_info))
                        
                        # 改进后的图片嵌入方式
                        relative_image_path = f"./images/{file_path.stem}/{image_info['name']}"
                        content += (
                            f"```image\n"
                            f"path: {relative_image_path}\n"
                            f"name: {image_info['name']}\n"
                            f"description: {image_description}\n"
                            f"```\n\n"
                        )
        
        # 保存Markdown内容到文件
        markdown_file = self.markdown_dir / (file_path.stem + ".md")
        markdown_file.parent.mkdir(parents=True, exist_ok=True)
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # 将Markdown内容分割成语义分块
        chunks = parse_document_content(content, chunk_size=4096)  # 示例分块大小
        
        # 创建分块目录
        chunks_dir = self.chunks_dir / str(file_path.stem)
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            # 保存分块到文件
            chunk_file = chunks_dir / f"chunk_{i+1}.md"
            print("分割后的语义块：")
            print(chunk['headings'])
            print(chunk['content'])
            print("="*50)  # 分隔符，方便查看不同块的内容f
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(str(chunk['headings']) + '\n'*2 + str(chunk['content']) + '\n'*2)
            
            # 创建带实际文件路径的DocumentChunk
            chunk_objects.append(
                DocumentChunk(
                    hash=DocumentItem.compute_hash(str(chunk).encode("utf-8")),
                    evidence_type = "markdown",
                    collector = self.collector,
                    project = self.project,
                    url=str(chunk_file),
                    content=chunk,
                    index=i+1
                )
            )

        # 计算整个文档的哈希值
        document_hash = DocumentItem.compute_hash(content.encode("utf-8"))

        # 创建DocumentItem
        document_item = DocumentItem(
            hash=document_hash,
            url=str(self.markdown_dir / file_path.stem),
            chunks=chunk_objects,
            images=images
        )

        # 保存证据JSON到data/evidence.json
        evidence_file = Path("data/evidence.json")
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成证据数据
        evidence_data = document_item.to_evidence_json(file_path.name)
        
        # 如果文件存在则读取现有证据
        existing_evidence = []
        if evidence_file.exists():
            with open(evidence_file, 'r', encoding='utf-8') as f:
                existing_evidence = json.load(f)
        
        # 追加新证据数据
        existing_evidence.extend(evidence_data)
        
        # 写入更新后的证据数据
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(existing_evidence, f, ensure_ascii=False, indent=2)

        return document_item
    
    def parse_document(self, file_path: Path) -> DocumentItem:
        """解析单个文档为结构化的DocumentItem格式
        
        Args:
            file_path: 要解析的文档路径
            
        Returns:
            DocumentItem: 包含内容、分块和图片的结构化文档数据
        """
        # 创建文档专用目录
        doc_markdown_dir = self.markdown_dir / file_path.stem
        doc_images_dir = self.images_dir / file_path.stem
        doc_chunks_dir = self.chunks_dir / file_path.stem
        doc_extracted_dir = self.extracted_dir / file_path.stem
        
        doc_markdown_dir.mkdir(parents=True, exist_ok=True)
        doc_images_dir.mkdir(parents=True, exist_ok=True)
        doc_chunks_dir.mkdir(parents=True, exist_ok=True)
        doc_extracted_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据文件格式分发到对应的解析器
        if file_path.suffix.lower() == '.docx':
            return self.parse_docx(file_path)
        elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            # 处理独立图片文件
            return self.parse_standalone_image(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")

    def convert(self):
        """将源目录中的所有文档转换为markdown格式"""
        # 创建输出目录（如果不存在）
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        
        # 处理源目录中的每个文件
        for file_path in self.source_dir.iterdir():
            if file_path.is_file():
                self.parse_document(file_path)
        
        # 如果启用了清理选项，则清空源目录
        if self.cleanup:
            for item in self.source_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

    def parse_image(self, image_path: Path) -> str:
        """解析独立图片文件并返回markdown格式的图片块
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: markdown格式的图片块，包含图片信息和base64编码内容
        """
        try:
            # 确保图片是PNG格式
            if image_path.suffix.lower() not in ['.png']:
                with Image.open(image_path) as img:
                    png_path = image_path.with_suffix('.png')
                    img.save(png_path, 'PNG')
                    image_path = png_path
            
            # 读取图片内容
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 生成图片信息
            image_hash = hashlib.sha256(image_data).hexdigest()
            image_name = image_path.name
            image_content = base64.b64encode(image_data).decode('utf-8')
            
            # 构建markdown图片块
            return f"""```image
            path: {str(image_path)}
            name: {image_name}
            description: 独立图片文件
            content: {image_content}
            hash: {image_hash}
            ```"""
        
        except Exception as e:
            logger.error(f"解析图片失败: {str(e)}")
            return ""

    def parse_standalone_image(self, image_path: Path) -> DocumentImage:
        """处理独立图片文件
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            DocumentImage: 包含图片信息的对象
        """
        # 读取图片内容并生成哈希
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_hash = hashlib.sha256(image_data).hexdigest()
        
        # 返回DocumentImage对象
        return DocumentImage(
            hash=image_hash,
            url=str(image_path),
            name=image_path.name,
            collector=self.collector,
            project=self.project,
            evidence_type="image",
            description=self.parse_image(image_path)  # 将markdown描述存入description字段
        )

if __name__ == '__main__':
    parser = DocumentParser(cleanup=False)
    parser.convert()
