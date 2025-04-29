from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class UploadResponse(BaseModel):
    file_path: str
    raw_text: str

class SimplifyRequest(BaseModel):
    raw_text: str
    language: str

class validateRequest(BaseModel):
    simplified_text: str
    original_text: str

class validateResponse(BaseModel):
    simplified_text: str
    is_valid: bool
    explanation: str

class FhirRequest(BaseModel):
    summary: str
    instructions: List[str]
    importance: List[str]
    follow_up: List[str]
    medications: List[str]
    precautions: List[str]
    references: List[str]
    disclaimer: str
    patient_id: Optional[str] = None
    author_reference: Optional[str] = None

class SimplifyResponse(BaseModel):
    summary: str
    instructions: List[str]
    importance: List[str]
    follow_up: List[str]
    medications: List[str]
    precautions: List[str]
    references: List[str]
    disclaimer: str   

class ChatRequest(BaseModel):
    user_id: str
    user_message: str
    context: list[str]           # note: a single string of all your simplified notes

class ChatResponse(BaseModel):
    reply: str