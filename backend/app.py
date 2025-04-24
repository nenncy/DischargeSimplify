from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .models import UploadResponse, SimplifyRequest, SimplifyResponse, ChatRequest, ChatResponse
from .utils import save_file_locally, extract_text_from_file, categorize
from .prompt_engineer import simplify_instructions, generate_concise_summary
import os, json, time, random, requests, asyncio
from pycountry import languages

# Load environment
load_dotenv()

OR_KEY = os.getenv("OPENROUTER_API_KEY")
OR_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload", response_model=UploadResponse)
def upload_file(file: UploadFile = File(...)):
    try:
        file_path = save_file_locally(file)
        raw_text = extract_text_from_file(file_path)
        return {"file_path": file_path, "raw_text": raw_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simplify", response_model=SimplifyResponse)
async def simplify(req: SimplifyRequest):
    instr, imp, fu, meds, precs, refs = simplify_instructions(req.raw_text, req.language, req.reading_level)
    sections = categorize(req.raw_text, instr, imp, fu, meds, precs, refs)
    concise = generate_concise_summary(req.raw_text, req.language, req.reading_level)
    return {
        "concise_summary": concise,
        "instructions": instr,
        "importance":   imp,
        "follow_up":    fu,
        "medications":  meds,
        "precautions":  precs,
        "references":   refs,
        "sections": sections, 
    } 
    
@app.post("/assistant/chat", response_model=ChatResponse)
async def assistant_chat(req: ChatRequest):
    headers = {"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"}
    prompt = (
        "You are a professional medical assistant. "
        "Use patient-friendly language, avoid jargon, and be concise. "
        "You MUST answer questions *only* from the provided 'context'"
        "of simplified instructions. If the answer is not in that context, reply “I’m sorry, I don’t have that information.”"
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "system", "content": f"Discharge summary:\n{req.concise_summary}"}
    ]
    for heading, items in req.sections.items():
        section_text = f"{heading}:\n" + "\n".join(items)
        messages.append({"role": "system", "content": section_text})
    messages.append({"role": "user", "content": req.user_message})
    payload = {
        "model": "openai/o4-mini",
        "messages": messages,
        "temperature": 0.0
    }
    try:
        resp = requests.post(OR_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # extract assistant reply
        reply = data["choices"][0]["message"]["content"].strip()
        return {"reply": reply}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"OpenRouter error: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok"}