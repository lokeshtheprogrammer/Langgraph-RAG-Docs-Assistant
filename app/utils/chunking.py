from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logging import logger


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split raw text into chunks using RecursiveCharacterTextSplitter."""
    if not text:
        return []

    logger.info(f"Splitting text of length {len(text)} characters (size={chunk_size}, overlap={chunk_overlap})...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "```", ".", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = splitter.split_text(text)
    logger.info(f"Generated {len(chunks)} chunks from source text.")
    return chunks
