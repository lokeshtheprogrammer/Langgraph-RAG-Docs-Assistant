import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logging import logger


def split_text(text: str, chunk_size: int, chunk_overlap: int, filename: str | None = None) -> list[str]:
    """Split raw text into chunks using a Markdown header-aware two-pass splitter."""
    if not text:
        return []

    logger.info(f"Splitting text of length {len(text)} characters (size={chunk_size}, overlap={chunk_overlap})...")

    # Step 1: Split on Markdown headers (#, ##, ###, etc.) and horizontal rules (---)
    header_regex = re.compile(r'^(#{1,6})\s+(.+)$')
    lines = text.splitlines()
    sections = []
    
    current_headers = [""] * 6  # levels 1 to 6
    current_section_lines = []
    
    for line in lines:
        stripped = line.strip()
        match = header_regex.match(stripped)
        is_hr = stripped in ("---", "***", "___")
        
        if match or is_hr:
            if current_section_lines:
                sections.append({
                    "headers": [h for h in current_headers if h],
                    "content": "\n".join(current_section_lines)
                })
                current_section_lines = []
            
            if match:
                level = len(match.group(1))
                header_name = match.group(2).strip()
                current_headers[level - 1] = header_name
                # Reset lower levels
                for i in range(level, 6):
                    current_headers[i] = ""
            current_section_lines.append(line)
        else:
            current_section_lines.append(line)
            
    if current_section_lines:
        sections.append({
            "headers": [h for h in current_headers if h],
            "content": "\n".join(current_section_lines)
        })

    if not sections:
        sections = [{"headers": [], "content": text}]

    final_chunks = []
    
    for sec in sections:
        headers = sec["headers"]
        prefix = ""
        if filename:
            prefix += f"Document: {filename}\n"
        if headers:
            prefix += f"Section: {' > '.join(headers)}\n"
        if prefix:
            prefix += "---\n"
            
        content = sec["content"]
        
        # Check if the prefix + content fits in chunk_size
        if len(prefix) + len(content) <= chunk_size:
            final_chunks.append(prefix + content)
        else:
            # Fallback split of large section content
            # Account for prefix length in the chunk_size
            adjusted_chunk_size = max(chunk_size - len(prefix), chunk_overlap + 1)
            
            temp_splitter = RecursiveCharacterTextSplitter(
                chunk_size=adjusted_chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", "```", ".", " ", ""],
                length_function=len,
                is_separator_regex=False,
            )
            
            sub_chunks = temp_splitter.split_text(content)
            for sc in sub_chunks:
                final_chunks.append(prefix + sc)
                
    logger.info(f"Generated {len(final_chunks)} chunks from source text.")
    return final_chunks

