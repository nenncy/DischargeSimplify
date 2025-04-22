from pydantic import BaseModel
from typing import List, Dict, Any

class UploadResponse(BaseModel):
    file_path: str
    raw_text: str

class SimplifyRequest(BaseModel):
    raw_text: str
    language: str

class SimplifyResponse(BaseModel):
    instructions: List[str]
    importance:   List[str]
    follow_up:    List[str]
    medications:  List[str]
    precautions:  List[str]
    references:   List[str]