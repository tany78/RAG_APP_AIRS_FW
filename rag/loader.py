from pathlib import Path
from typing import List, Dict
import docx
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: Path) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file_path: Path) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def chunk_text(text: str, max_tokens: int = 300) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunk = " ".join(words[i:i + max_tokens])
        chunks.append(chunk)
    return chunks

def load_document(file_path: Path) -> List[Dict]:
    if file_path.suffix == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif file_path.suffix == ".docx":
        raw_text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type")

    text_chunks = chunk_text(raw_text)
    return [{"text": chunk, "metadata": {"source": file_path.name, "chunk": i}} 
            for i, chunk in enumerate(text_chunks)]
