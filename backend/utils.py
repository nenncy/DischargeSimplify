import os
import re
import json
from fastapi import UploadFile
from pdfminer.high_level import extract_text as pdf_extract

# Directory to store uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

def save_file_locally(uploaded_file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.filename)
    # Read file content from UploadFile's internal buffer
    content = uploaded_file.file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from .txt, .json, or .pdf at file_path.

    - JSON: returns 'raw_text' or 'text' key, or a full JSON dump.
    - PDF: uses PyPDF2 to extract all page text.
    - Others: decodes bytes as UTF-8, falling back to Latin-1.
    """
    ext = file_path.lower().rsplit('.', 1)[-1]
    # JSON
    if ext == 'json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('raw_text') or data.get('text') or json.dumps(data, ensure_ascii=False)
    # PDF
    elif ext == 'pdf':
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise RuntimeError('PDF support requires PyPDF2. Install via `pip install PyPDF2`.')
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return '\n'.join(pages)
    # Other plain-text
    else:
        with open(file_path, 'rb') as f:
            raw = f.read()
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            return raw.decode('latin-1', errors='ignore')
        
def categorize(raw_text, instructions, importance, follow_up, medications, precautions, references):
    sections = {
        "Instructions": instructions,
        "Importance": importance,
        "Follow-Up": follow_up,
        "Medications": medications,
        "Precautions": precautions,
        "References": references
    }
    priority = ["Medications", "Precautions", "Follow-Up", "Importance", "Instructions", "References"]
    first_seen = {}
    for sec in priority:
        for itm in sections.get(sec, []):
            if itm not in first_seen:
                first_seen[itm] = sec
    for sec in sections:
        sections[sec] = [itm for itm in sections[sec] if first_seen.get(itm) == sec]
    return sections