from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .models import UploadResponse, SimplifyRequest, SimplifyResponse
from .utils import save_file_locally, extract_text_from_file, categorize
from .prompt_engineer import simplify_instructions, generate_concise_summary
import os
from pycountry import languages


# Load environment
load_dotenv()

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
def simplify(req: SimplifyRequest):
    instr, imp, fu, meds, precs, refs = simplify_instructions(req.raw_text, req.language, req.reading_level)
    sections = categorize(req.raw_text, instr, imp, fu, meds, precs, refs)
    concise = generate_concise_summary(req.raw_text, req.language)
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
    
@app.get("/health")
def health_check():
    return {"status": "ok"}