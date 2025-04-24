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
    ext = file_path.lower().rsplit(".", 1)[-1]
    if ext == "json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("raw_text") or data.get("text") or json.dumps(data)
    elif ext == "pdf":
        return pdf_extract(file_path)
    else:
        # try utf-8, fallback to latin-1
        with open(file_path, "rb") as f:
            raw = f.read()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1", errors="ignore")

        
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