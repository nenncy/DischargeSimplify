import os
import asyncio
import openai
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from fhirconvertion import convert_to_composition
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
from models import (UploadResponse,SimplifyRequest,SimplifyResponse,ChatRequest,ChatResponse,validateRequest,validateResponse,FhirRequest, InstructionVersion, InstructionVersionCreate, InstructionVersionResponse)
from utils import save_file_locally, extract_text_from_file
from prompt_engineer import simplify_instructions, validate_instructions, build_simplify_prompt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal
from models import InstructionVersion, InstructionVersionCreate, InstructionVersionResponse

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()
@app.post("/discharge_instructions/", response_model=InstructionVersionResponse)
def create_instruction(instruction: InstructionVersionCreate, db: Session = Depends(get_db)):
    db_instruction = InstructionVersion(**instruction.dict())
    db.add(db_instruction)
    db.commit()
    db.refresh(db_instruction)
    return db_instruction

@app.get("/discharge_simplify/", response_model=list[InstructionVersionResponse])
def get_all_instructions(db: Session = Depends(get_db)):
    instructions = db.query(InstructionVersion).all()
    return instructions


# Initialize FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Async client for assistant chat
client = AsyncOpenAI(api_key=openai.api_key)

@app.post("/upload", response_model=UploadResponse)
def upload_file(file: UploadFile = File(...)):
    try:
        file_path = save_file_locally(file)
        raw_text = extract_text_from_file(file_path)
        return {"file_path": file_path, "raw_text": raw_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simplify", response_model=SimplifyResponse)
def simplify(req: SimplifyRequest):
    print("🔍 Received simplify request: language =", req.language)
    summary, instr, imp, fu, meds, precs, refs, disclaimer = simplify_instructions(
        req.raw_text)
    return {
        "summary":      summary,
        "instructions": instr,
        "importance":   imp,
        "follow_up":    fu,
        "medications":  meds,
        "precautions":  precs,
        "references":   refs,
        "disclaimer":   disclaimer,
    }

@app.post("/simplify_stream")
async def simplify_stream(req: SimplifyRequest):
    prompt = build_simplify_prompt(req.raw_text, req.language)

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        top_p=1.0,
        stream=True,
    )

    async def event_generator():
        for chunk in response:
            delta = chunk.choices[0].delta.get("content")
            if delta:
                yield delta

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/assistant/chat", response_model=ChatResponse)
async def assistant_chat(req: ChatRequest):
    msg = req.user_message.strip().lower()
    if msg in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}:
        return ChatResponse(reply="👋 Hello! I’m your Discharge-Helper Assistant. How can I help you today?")
    if msg in {"thanks", "thank you", "thx", "ty"}:
        return ChatResponse(reply="You’re very welcome! Let me know if there’s anything else I can do.")

    # 1) create thread
    thread = await client.beta.threads.create()
    

    # 2) post context+question as a single user message
    combined = (
        "Context (simplified instructions):\n"
        + "\n".join(req.context)
        + "\n\nUser Question:\n"
        + req.user_message
    )
    await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=combined
    )

    # 3) run the assistant
    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # 4) poll until it’s done
    while run.status not in ("completed", "failed"):
        await asyncio.sleep(0.5)
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )

    if run.status != "completed":
        raise HTTPException(500, f"Assistant run failed: {run.status}")

    # 5) fetch the messages and return the assistant’s response
    msgs = await client.beta.threads.messages.list(thread_id=thread.id)
    assistant_msg = next(
        (m.content[0].text.value for m in msgs.data if m.role == "assistant"),
        ""
    )
    return {"reply": assistant_msg}

@app.post("/validate", response_model=validateResponse)
def validate(req: validateRequest):
    is_valid, explanation, simplified_text = validate_instructions(
        req.original_text,
        req.simplified_text
    )
    # You can log or manipulate ans if needed
    return {
        "is_valid":      is_valid,
        "explanation":   explanation,
        "simplified_text": simplified_text,
    }
    
@app.post("/to_fhir")
async def to_fhir(payload: FhirRequest):
    try:
        data = payload.dict(exclude={"patient_id", "author_reference"})
        comp = convert_to_composition(
            data,
            patient_id=payload.patient_id,
            author_reference=payload.author_reference,
        )
        fhir_json = jsonable_encoder(comp, exclude_none=True)
        import json
        print("FHIR Composition JSON → ```json")
        print(json.dumps(fhir_json, indent=2))
        print("```")
        return fhir_json
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))   

@app.get("/health")
def health_check():
    return {"status": "ok"}