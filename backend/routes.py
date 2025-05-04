from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal
from models import InstructionVersion, InstructionVersionCreate, InstructionVersionResponse

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/discharge_instructions/", response_model=InstructionVersionResponse)
def create_instruction(instruction: InstructionVersionCreate, db: Session = Depends(get_db)):
    db_instruction = InstructionVersion(**instruction.dict())
    db.add(db_instruction)
    db.commit()
    db.refresh(db_instruction)
    return db_instruction

@router.get("/discharge_simplify/", response_model=list[InstructionVersionResponse])
def get_all_instructions(db: Session = Depends(get_db)):
    instructions = db.query(InstructionVersion).all()
    return instructions
