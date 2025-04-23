from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import UploadResponse, SimplifyRequest, SimplifyResponse , validateRequest , validateResponse
from utils import save_file_locally, extract_text_from_file
from prompt_engineer import simplify_instructions, validate_instructions
import os

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
    instr, imp, fu, meds, precs, refs = simplify_instructions(req.raw_text, req.language)
    return {
        "instructions": instr,
        "importance":   imp,
        "follow_up":    fu,
        "medications":  meds,
        "precautions":  precs,
        "references":   refs,
    }

@app.post("/validate", response_model=validateResponse)
def validate(req: validateRequest):
    is_valid, explanation, simplified_text = validate_instructions(req.original_text, req.simplified_text)
    ans = {
        "is_valid": is_valid,
        "explanation": explanation,
        "simplified_text": simplified_text,

    }
    # Check if the response is valid    
    print(ans, "***********")
    return {
        "is_valid": is_valid,
        "explanation": explanation,
        "simplified_text": simplified_text,
        # "original_text": original_text
    }
   

@app.get("/health")
def health_check():
    return {"status": "ok"}