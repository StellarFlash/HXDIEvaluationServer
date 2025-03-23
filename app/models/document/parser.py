import os
import shutil
import hashlib
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import re
from typing import List
from docx import Document
from datetime import datetime
import json
from app.models.document.models import DocumentImage, DocumentChunk, DocumentItem
from app.models.document.utils import get_outline_level, extract_image_from_run, split_markdown_by_semantics
from app.utils.maas_client import vision_completion

class DocumentParser:
    """Parser for converting documents to markdown format"""
    
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
        """Parse docx file into structured DocumentItem format
        
        Args:
            file_path: Path to the docx file
            output_dir: Directory to save extracted images
            
        Returns:
            DocumentItem: Structured document data including content, chunks and images
        """
        doc = Document(file_path)
        content = ""
        images = []
        image_counter = 0

        # Process each paragraph
        for paragraph in doc.paragraphs:
            # Determine paragraph outline level (if available)
            outline_level = get_outline_level(paragraph)
            if outline_level is not None:
                # Generate Markdown heading based on outline level
                content += "#" * outline_level + " " + paragraph.text.strip() + "\n\n"
                continue
            
            # Add normal paragraph text
            text = paragraph.text.strip()
            if text:
                content += text + "\n\n"
            
            # Process images in runs
            for run in paragraph.runs:
                if run.element.xpath('.//w:drawing'):
                    image_counter += 1
                    image_info = extract_image_from_run(doc, run, image_counter, self.images_dir / file_path.stem)
                    if image_info:
                        # Call VLM to generate image description
                        image_description = vision_completion(image_info['url'], prompt="你正在进行网络安全评估工作，需要从以下图片中提取出有助于评估的信息。")
                        
                        # Update image info with description
                        image_info["description"] = image_description
                        image_info["collector"] = self.collector
                        image_info["project"] = self.project
                        image_info["evidence_type"] = "image"
                        images.append(DocumentImage(**image_info))
                        
                        # Insert image placeholder with description
                        content += f"![{image_info['name']}]({image_info['name']})\n\n"
                        content += f"> 图片描述：{image_description}\n\n"

        # Split Markdown content into semantic chunks
        chunks = split_markdown_by_semantics(content, chunk_size=1000)  # Example chunk size
        
        # Create chunks directory
        chunks_dir = self.chunks_dir / str(file_path.stem)
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            # Save chunk to file
            chunk_file = chunks_dir / f"chunk_{i+1}.md"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk)
            
            # Create DocumentChunk with actual file path
            chunk_objects.append(
                DocumentChunk(
                    hash=DocumentItem.compute_hash(chunk.encode("utf-8")),
                    evidence_type = "markdown",
                    collector = self.collector,
                    project = self.project,
                    url=str(chunk_file),
                    content=chunk,
                    index=i+1
                )
            )

        # Compute overall document hash
        document_hash = DocumentItem.compute_hash(content.encode("utf-8"))

        # Create DocumentItem
        document_item = DocumentItem(
            hash=document_hash,
            url=str(self.markdown_dir / file_path.stem),
            chunks=chunk_objects,
            images=images
        )

        # Save evidence JSON to data/evidence.json
        evidence_file = Path("data/evidence.json")
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate evidence data
        evidence_data = document_item.to_evidence_json(file_path.name)
        
        # Read existing evidence if file exists
        existing_evidence = []
        if evidence_file.exists():
            with open(evidence_file, 'r', encoding='utf-8') as f:
                existing_evidence = json.load(f)
        
        # Append new evidence data
        existing_evidence.extend(evidence_data)
        
        # Write updated evidence data
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(existing_evidence, f, ensure_ascii=False, indent=2)

        return document_item
    
    def parse_document(self, file_path: Path) -> DocumentItem:
        """Parse a single document into structured DocumentItem format
        
        Args:
            file_path: Path to the document to parse
            
        Returns:
            DocumentItem: Structured document data including content, chunks and images
        """
        # Create document-specific directories
        doc_markdown_dir = self.markdown_dir / file_path.stem
        doc_images_dir = self.images_dir / file_path.stem
        doc_chunks_dir = self.chunks_dir / file_path.stem
        doc_extracted_dir = self.extracted_dir / file_path.stem
        
        doc_markdown_dir.mkdir(parents=True, exist_ok=True)
        doc_images_dir.mkdir(parents=True, exist_ok=True)
        doc_chunks_dir.mkdir(parents=True, exist_ok=True)
        doc_extracted_dir.mkdir(parents=True, exist_ok=True)
        
        # Dispatch to format-specific parser
        if file_path.suffix.lower() == '.docx':
            return self.parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def convert(self):
        """Convert all documents in source directory to markdown format"""
        # Create output directories if not exists
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each file in source directory
        for file_path in self.source_dir.iterdir():
            if file_path.is_file():
                self.parse_document(file_path)
        
        # Clear source directory if cleanup is enabled
        if self.cleanup:
            for item in self.source_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

if __name__ == '__main__':
    parser = DocumentParser(cleanup=False)
    parser.convert()
