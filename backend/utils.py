import os
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
    if file_path.lower().endswith('.pdf'):
        return pdf_extract(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()