from docx import Document
from typing import List, Tuple
from PIL import Image
import hashlib
import base64


# Helper function to get outline level of a paragraph
def get_outline_level(paragraph):
    """Get the outline level of a paragraph (1-based)."""
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

# Helper function to extract an image from a run
def extract_image_from_run(doc, run, image_counter, output_dir):
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            # Extract image extension and create output path
            image_ext = rel.target_ref.split(".")[-1]
            image_name = f"image_{image_counter}.png"
            image_path = output_dir / image_name

            # Save image
            with open(image_path, 'wb') as f:
                f.write(rel.target_part.blob)

            # Convert to PNG if needed
            if image_ext.lower() in ['jpg', 'jpeg']:
                with Image.open(image_path) as img_file:
                    img_file.save(image_path, 'PNG')

            # Create DocumentImage object
            return {
                "hash": hashlib.sha256(rel.target_part.blob).hexdigest(),
                "url": str(image_path),
                "content": base64.b64encode(rel.target_part.blob).decode('utf-8'),
                "name": image_name,
                "index": image_counter
            }
    return None

def split_markdown_by_semantics(markdown: str, chunk_size: int) -> List[str]:
    """
    Split a Markdown string into semantic chunks based on headings and content size.
    
    Args:
        markdown (str): The Markdown string to be split.
        chunk_size (int): Maximum size (in characters) of each chunk.
        
    Returns:
        List[str]: A list of semantic chunks.
    """
    def parse_markdown(lines: List[str]) -> List[Tuple[int, List[str]]]:
        """
        Parse the Markdown lines into a hierarchical structure.
        
        Args:
            lines (List[str]): Lines of the Markdown string.
            
        Returns:
            List[Tuple[int, List[str]]]: A list of tuples where each tuple contains
                the heading level and its associated lines.
        """
        parsed = []
        heading_stack = []  # Stack to track current heading path
        current_lines = []

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#"):
                # Save the previous section if exists
                if current_lines:
                    parsed.append((len(heading_stack), current_lines))
                    current_lines = []
                
                # Determine the heading level
                heading_level = len(stripped_line.split(" ")[0])
                
                # Update heading stack
                while len(heading_stack) >= heading_level:
                    heading_stack.pop()
                heading_stack.append(line)
            else:
                # Append content line with full heading path
                if line.strip():
                    if heading_stack:
                        # Add heading path as prefix
                        current_lines.extend(heading_stack)
                    current_lines.append(line)
        
        # Append the last section
        if current_lines:
            parsed.append((len(heading_stack), current_lines))
        
        return parsed

    def create_chunks(sections: List[Tuple[int, List[str]]], max_size: int) -> List[str]:
        """
        Recursively create chunks from the parsed sections.
        
        Args:
            sections (List[Tuple[int, List[str]]]): Parsed sections with heading levels.
            max_size (int): Maximum size (in characters) of each chunk.
            
        Returns:
            List[str]: A list of semantic chunks.
        """
        chunks = []
        for level, lines in sections:
            section_text = "\n".join(lines)
            if len(section_text) <= max_size:
                # If the section fits within the chunk size, add it directly
                chunks.append(section_text)
            else:
                # Split long sections while preserving heading context
                buffer = []
                current_size = 0
                for line in lines:
                    line_size = len(line) + 1  # +1 for newline
                    if current_size + line_size > max_size and buffer:
                        chunks.append("\n".join(buffer))
                        buffer = []
                        current_size = 0
                    buffer.append(line)
                    current_size += line_size
                if buffer:
                    chunks.append("\n".join(buffer))
        return chunks

    # Split the Markdown into lines and parse it
    lines = markdown.splitlines()
    parsed_sections = parse_markdown(lines)

    # Create chunks recursively
    return create_chunks(parsed_sections, chunk_size)
