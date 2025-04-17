from docx import Document
from typing import List, Tuple
from PIL import Image
import hashlib
import base64


# Helper function to get outline level of a paragraph
def get_outline_level(paragraph):
    """
    获取段落的大纲级别(1-based)
    
    参数:
        paragraph: docx文档中的段落对象
        
    返回:
        int: 段落的大纲级别(1-6)，如果无法确定则返回None
    """
    try:
        # First try to get outline level from paragraph style
        if hasattr(paragraph._element, 'pPr'):
            pPr = paragraph._element.pPr
            if hasattr(pPr, 'outlineLvl'):
                outline_lvl = pPr.outlineLvl.val
                return int(outline_lvl) + 1  # Convert 0-based to 1-based

        # Fallback: Try to guess outline level from heading style
        style_name = paragraph.style.name.lower()
        if 'heading' in style_name:
            # Extract heading level from style name (e.g. 'Heading 1' -> 1)
            try:
                level = int(style_name.split()[-1])
                return min(max(level, 1), 6)  # Ensure level is between 1-6
            except (ValueError, IndexError):
                pass

        # Fallback: Guess from text content (e.g. '### Heading' -> 3)
        text = paragraph.text.strip()
        if text.startswith('#'):
            level = len(text.split(' ')[0])
            return min(max(level, 1), 6)  # Ensure level is between 1-6

        return None
    except Exception:
        return None


def extract_image_from_run(doc, run, image_counter = 0, output_dir = 'images'):
    """
    从docx文档的特定run中提取图片
    
    参数:
        doc: Document对象
        run: 包含图片的run对象
        image_counter: 图片计数器，用于生成唯一文件名
        output_dir: 图片保存目录
        
    返回:
        dict: 包含图片信息的字典，格式为:
            {
                "hash": 图片内容的SHA256哈希值,
                "url": 图片保存路径,
                "content": 图片的base64编码内容,
                "name": 图片文件名,
                "index": 图片索引
            }
            如果没有找到图片则返回Nones
    """
    # 从run中获取drawing元素
    drawing = run.element.xpath('.//w:drawing')
    
    if not drawing:
        return None
        
    # 查找drawing元素的关系ID
    drawing = drawing[0]
    blip = drawing.xpath('.//a:blip')
    if not blip:
        return None
        
    rId = blip[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
    if not rId:
        return None
    
    # 根据ID查找关系
    rel = doc.part.rels.get(rId)
    if not rel or "image" not in rel.target_ref:
        return None
    
    # 处理图片
    image_ext = rel.target_ref.split(".")[-1]
    image_name = f"image_{image_counter}.png"
    image_path = output_dir / image_name

    # 保存图片
    with open(image_path, 'wb') as f:
        f.write(rel.target_part.blob)

    # 如果需要转换为PNG格式
    if image_ext.lower() in ['jpg', 'jpeg']:
        with Image.open(image_path) as img_file:
            img_file.save(image_path, 'PNG')
            
    # 创建图片信息对象
    return {
        "hash": hashlib.sha256(rel.target_part.blob).hexdigest(),
        "url": str(image_path),
        "content": base64.b64encode(rel.target_part.blob).decode('utf-8'),
        "name": image_name,
        "index": image_counter
    }

def parse_document_content(content="", chunk_size=4096):
    """
    解析文档内容并分割成语义块，保持标题层级关系和图片完整性
    """
    chunks = []
    current_chunk = []
    heading_stack = []
    lines = content.split('\n')
    
    def commit_chunk():
        """提交当前块到结果列表"""
        nonlocal current_chunk
        if current_chunk:
            chunks.append({
                'headings': [h['title'] for h in heading_stack],
                'content': '\n'.join(current_chunk).strip()
            })
            current_chunk = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 处理图片块 - 最高优先级
        if line.startswith('```image'):
            commit_chunk()  # 提交当前非图片内容块
            
            # 收集完整的图片块（包括开始和结束标记）
            image_block = [line]
            i += 1
            while i < len(lines) and not lines[i].strip() == '```':
                image_block.append(lines[i])
                i += 1
            
            if i < len(lines) and lines[i].strip() == '```':
                image_block.append(lines[i])
                i += 1
            
            # 提取图片路径作为标题
            image_path = None
            for bline in image_block:
                if bline.strip().startswith('path:'):
                    image_path = bline.split(':', 1)[1].strip()
                    break
            
            chunks.append({
                'headings': [h['title'] for h in heading_stack] + [f"图片: {image_path}" if image_path else "图片"],
                'content': '\n'.join(image_block)
            })
            continue
            
        # 处理标题行
        if line.startswith('#'):
            level = line.count('#')
            title = line.lstrip('#').strip()
            
            # 遇到同级或更高级标题时提交当前块
            while heading_stack and heading_stack[-1]['level'] >= level:
                commit_chunk()
                heading_stack.pop()
                
            heading_stack.append({'level': level, 'title': title})
            commit_chunk()
            
        elif line:  # 非空行
            current_chunk.append(line)
            
        i += 1
    
    commit_chunk()  # 提交最后一个块
    
    # 合并小切片（保持原有逻辑）
    merged_chunks = []
    i = 0
    while i < len(chunks):
        current = chunks[i]
        if i < len(chunks) - 1 and len(current['content']) < chunk_size // 2:
            next_chunk = chunks[i + 1]
            # 检查标题层级相同且都不是图片块
            if (current['headings'] == next_chunk['headings'] and
                not current['content'].startswith('```image') and
                not next_chunk['content'].startswith('```image')):
                
                merged_content = current['content'] + '\n' + next_chunk['content']
                if len(merged_content) <= chunk_size:
                    merged_chunks.append({
                        'headings': current['headings'],
                        'content': merged_content
                    })
                    i += 2
                    continue
        merged_chunks.append(current)
        i += 1
    
    return merged_chunks

if __name__ == "__main__":
    # 示例用法
    markdown_path = "data/document/markdown/材料补充 - 区公司核心网 - 已补充 - 副本.md"
    # 一级标题
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    # 分割Markdown
    chunks = parse_document_content(markdown_content)
    for chunk in chunks:
        print("分割后的语义块：")
        print(chunk['headings'])
        print(chunk['content'])
        print("="*50)  # 分隔符，方便查看不同块的内容f