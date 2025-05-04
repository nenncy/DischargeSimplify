from fastapi import UploadFile
from pdfminer.high_level import extract_text as pdf_extract
import os, json, openai, time, random
from dotenv import load_dotenv, find_dotenv
from ratelimit import limits, sleep_and_retry
from openai import RateLimitError
import re
_ = load_dotenv(find_dotenv(), override=True)
print("🔑 Using OPENAI_API_KEY=", os.getenv("OPENAI_API_KEY"))

openai.api_key = os.getenv("OPENAI_API_KEY")

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 20
# Directory to store uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

def save_file_locally(uploaded_file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.filename)
    # Read file content from UploadFile's internal buffer
    content = uploaded_file.file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path

def extract_text_from_file(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        return pdf_extract(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def _call_openai_with_rate_limit(prompt: str, model: str = "gpt-4o", temperature: float = 0.0, top_p: float = 1.0) -> openai.ChatCompletion:
    """Call OpenAI, automatically sleeping if you exceed MAX_CALLS_PER_MINUTE."""
    try:
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p
        )
    except AttributeError:
        # fallback for older clients
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p
        )

def extract_json(raw_output: str) -> dict:
    """
    Safely extracts and parses JSON from an LLM response.
    Handles Markdown-style triple backticks and non-JSON text.
    """
    if not raw_output.strip():
        raise ValueError("LLM returned an empty response.")

    # Remove triple backticks and extract only JSON content
    match = re.search(r"\{[\s\S]+\}", raw_output)
    if match:
        raw_output = match.group(0)

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM: {e}\nRaw output:\n{raw_output}")
    
