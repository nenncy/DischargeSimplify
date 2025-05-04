import os
import json
import time
import openai
from dotenv import load_dotenv, find_dotenv
from ratelimit import limits, sleep_and_retry
from openai import RateLimitError
from utils import extract_json
from validation_layer import chunk_text, build_faiss_index, validate_and_filter_fields

# ─── Load environment ─────────────────────────────────────────────────────────
load_dotenv(find_dotenv(), override=True)
print("🔑 Using OPENAI_API_KEY=", os.getenv("OPENAI_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")

# ─── Rate limit settings ─────────────────────────────────────────────────────
ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 20

@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def _call_openai(prompt: str, model: str = "gpt-4o", temperature: float = 0.0, top_p: float = 1.0) -> openai.ChatCompletion:
    """Call OpenAI with automatic rate-limit back-off."""
    try:
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
        )
    except (AttributeError, RateLimitError):
        time.sleep(1)
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
        )

def build_simplify_prompt(text: str) -> str:
    """
    Assemble the prompt for simplifying instructions.
    """
    return (
        "You are a specialized medical discharge instruction simplifier.\n"
        "Follow these steps in order:\n"
        f"1. Simplify thsoe medical discharge instruction into clear, patient-friendly language at a 6th-grade reading level\n"
        f"2. Format the simplified content into the JSON structure specified below\n\n"
        "CRITICAL MEDICAL GUIDELINES:\n"
        "1. Only simplify information present in the original text\n"
        "2. Never invent new medical instructions or medications\n"
        "3. Maintain all medically relevant details while simplifying language\n"
        "4. Each bullet point must be under 20 words and crystal clear\n\n"
        "Output ONLY a valid JSON object with exactly these keys (KEEP THESE KEYS IN ENGLISH):\n"
        f" \"Summary\": a concise, coherent paragraph (5–7 sentences) in the selected language that explains why you were discharged, states the key diagnosis, and highlights the most important next steps.\n"        
        f" \"Instructions\": array of bullet-point instructions in selected language derived from the text.\n"
        f" \"Importance\": array explaining in selected language why following each instruction is important for health.\n"
        f" \"FollowUpTasks\": array of follow-up tasks or visits in selected language. If none explicitly mentioned, include standard follow-up recommendations relevant to the condition.\n"
        f" \"Medications\": object with two sub-arrays (VALUES IN selected language, KEEP THESE SUB-KEYS IN ENGLISH):\n"
        f"    \"ToTake\": array of medications to take with dosage and purpose in selected language.\n"
        f"    \"ToAvoid\": array of medications and substances to avoid with brief explanation why in selected language.\n"
        f" \"Precautions\": array of warning signs or activities to avoid in selected language based on the condition implied in the instructions.\n"
        f" \"References\": array of brief explanations in selected language supporting the instructions.\n"
        f" \"Disclaimer\": medical disclaimer in selected language stating this is not professional advice.\n\n"
        "STRICT REQUIREMENTS:\n"
        f"1. ALL JSON KEYS MUST REMAIN IN ENGLISH EXACTLY AS SHOWN: \"Summary\", \"Instructions\", \"Importance\", \"FollowUpTasks\", \"Medications\", \"ToTake\", \"ToAvoid\", \"Precautions\", \"References\", \"Disclaimer\"\n"
        "2. EVERY section above MUST contain meaningful content - NO empty arrays or objects allowed\n"
        "3. The Medications object MUST contain both ToTake and ToAvoid sub-arrays, each with at least one item\n"
        "4. Clearly distinguish between medications to take versus medications to avoid\n"
        "5. If no medications to take are explicitly mentioned, provide general medication guidance relevant to the condition\n"
        "6. If no medications to avoid are explicitly mentioned, include standard contraindications for the identified condition\n\n"
        "7. For **each** bullet across **all** sections, analyze its core fact **and** its intended purpose—assign it to the single JSON section whose intent best matches that bullet, and remove any duplicates or misplaced items across Summary, Instructions, Importance, FollowUpTasks, Medications (ToTake/ToAvoid), Precautions, References, and Disclaimer\n\n"        f"1. ALL JSON KEYS IN ENGLISH\n"
        f"{text}\n"
    )

def simplify_instructions(text: str):
    """
    Simplify discharge instructions into patient-friendly language.
    Returns: summary, instructions, importance, follow_up_tasks, medications, precautions, references, disclaimer
    """
    prompt = build_simplify_prompt(text)
    resp = _call_openai(prompt)
    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    print("LLM RAW JSON →", raw)

    try:
        obj = extract_json(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nRaw output:\n{raw}")

    # Skip FAISS here; return full raw JSON
    return (
        obj.get("Summary", ""),
        obj.get("Instructions", []),
        obj.get("Importance", []),
        obj.get("FollowUpTasks", []),
        obj.get("Medications", []),
        obj.get("Precautions", []),
        obj.get("References", []),
        obj.get("Disclaimer", "")
    )

def validate_instructions(original_text: str, simplified_text: str):
    """
    Check whether the simplified instruction is supported by the original text by querying the LLM.
    Returns: (is_valid: bool, explanation: str, simplified_text: str)
    """
    prompt = (
        "You are a diligent medical assistant tasked with validating simplified discharge instructions."
        "Given the ORIGINAL instructions and a SINGLE simplified instruction, determine if the simplified version is directly supported or reasonably inferred from the original."
        "Return a JSON object with the keys:"
        "  \"is_valid\": true or false,"
        "  \"explanation\": a brief explanation citing the source segment from the original instructions."
        "Only output valid JSON (no extra text)."
        f"ORIGINAL:{original_text}"
        f"SIMPLIFIED:{simplified_text}"
    )
    # Call LLM
    resp = _call_openai(prompt)
    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    # Parse JSON
    try:
        obj = extract_json(raw)
    except json.JSONDecodeError:
        # Fallback if LLM misformats
        return False, f"Invalid JSON from validation LLM: {raw}", simplified_text

    is_valid = obj.get("is_valid", False)
    explanation = obj.get("explanation", "")
    return is_valid, explanation, simplified_text