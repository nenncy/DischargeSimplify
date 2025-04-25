import os
import asyncio
import openai
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from models import (
    UploadResponse,
    SimplifyRequest,
    SimplifyResponse,
    ChatRequest,
    ChatResponse,
    validateRequest,
    validateResponse,
)
from utils import save_file_locally, extract_text_from_file
from prompt_engineer import simplify_instructions, validate_instructions

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Initialize FastAPI
app = FastAPI()
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
        req.raw_text,
        req.language
    )
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


@app.post("/assistant/chat", response_model=ChatResponse)
async def assistant_chat(req: ChatRequest):
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


@app.get("/health")
def health_check():
    return {"status": "ok"}