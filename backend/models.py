from pydantic import BaseModel
from typing import List, Dict, Any

class UploadResponse(BaseModel):
    file_path: str
    raw_text: str

class SimplifyRequest(BaseModel):
    raw_text: str
    language: str

class SimplifyResponse(BaseModel):
    summary: str
    precautions: List[str]
    medications: List[Any] 