from pydantic import BaseModel
from typing import List, Dict, Any

class UploadResponse(BaseModel):
    file_path: str
    raw_text: str

class SimplifyRequest(BaseModel):
    raw_text: str
    language: str
    reading_level: int

class SimplifyResponse(BaseModel):
    concise_summary: str 
    instructions: List[str]
    importance:   List[str]
    follow_up:    List[str]
    medications:  List[str]
    precautions:  List[str]
    references:   List[str]
    sections:     Dict[str,List[str]]
