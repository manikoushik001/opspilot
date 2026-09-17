import re
from typing import List, Dict, Any


def clean_text(text: str) -> str:
    """Normalize whitespace and strip unnecessary characters."""
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\t', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping semantic chunks.
    Preserves paragraph and sentence boundaries where possible.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    # Split by paragraphs or double newlines first
    paragraphs = re.split(r'\n\s*\n', cleaned)
    chunks: List[Dict[str, Any]] = []
    current_chunk = ""
    chunk_idx = 0

    base_meta = metadata or {}

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) <= chunk_size:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "content": current_chunk,
                    "metadata": {**base_meta, "chunk_index": chunk_idx}
                })
                chunk_idx += 1

            # If the paragraph itself is longer than chunk_size, split by sentences
            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= chunk_size:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            chunks.append({
                                "chunk_index": chunk_idx,
                                "content": current_chunk,
                                "metadata": {**base_meta, "chunk_index": chunk_idx}
                            })
                            chunk_idx += 1
                        current_chunk = sentence
            else:
                current_chunk = para

    if current_chunk:
        chunks.append({
            "chunk_index": chunk_idx,
            "content": current_chunk,
            "metadata": {**base_meta, "chunk_index": chunk_idx}
        })

    return chunks
