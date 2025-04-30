from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from pydantic import BaseModel

Base = declarative_base()

# SQLAlchemy ORM Model (maps to your InstructionVersions table)
class InstructionVersion(Base):
    __tablename__ = "InstructionVersions"

    UniqueID = Column(Integer, primary_key=True, index=True)
    OriginalInstruction = Column(Text, nullable=False)
    SimplifiedInstruction = Column(Text)
    LanguageBasedInstruction = Column(Text)
    EHRIntegrationJSON = Column(Text)
    Language = Column(String(50))
    CreatedAt = Column(DateTime, server_default=func.now())

# Pydantic Models (for API Input/Output)
class InstructionVersionCreate(BaseModel):
    OriginalInstruction: str
    SimplifiedInstruction: str
    LanguageBasedInstruction: str
    EHRIntegrationJSON: str
    Language: str

class InstructionVersionResponse(BaseModel):
    UniqueID: int
    OriginalInstruction: str
    SimplifiedInstruction: str
    LanguageBasedInstruction: str
    EHRIntegrationJSON: str
    Language: str
    CreatedAt: datetime 

    class Config:
        orm_mode = True
        json_encoders = {
            datetime   : lambda v: v.isoformat()
         }


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