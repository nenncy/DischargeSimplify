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
def _call_openai(prompt: str, model: str = "gpt-4o", temperature: float = 0.7):
    """Call OpenAI with automatic rate-limit back-off."""
    try:
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
    except (AttributeError, RateLimitError):
        time.sleep(1)
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )


def build_simplify_prompt(text: str, language: str = "English") -> str:
    """
    Assemble the prompt for simplifying instructions.
    """
    return (
        "You are a specialized medical discharge instruction translator and simplifier.\n"
        f"CRITICAL: ALL CONTENT MUST BE IN {language.upper()}, BUT KEEP JSON KEYS IN ENGLISH.\n\n"
        "Follow these steps in order:\n"
        f"1. First, carefully translate every word of the discharge instructions into {language}\n"
        f"2. Then simplify that {language} translation into clear, patient-friendly language at a 6th-grade reading level\n"
        f"3. Format the simplified {language} content into the JSON structure specified below\n\n"
        "CRITICAL MEDICAL GUIDELINES:\n"
        "1. Only simplify information present in the original text\n"
        "2. Never invent new medical instructions or medications\n"
        "3. Maintain all medically relevant details while simplifying language\n"
        "4. Each bullet point must be under 20 words and crystal clear\n\n"
        "Output ONLY a valid JSON object with exactly these keys (KEEP THESE KEYS IN ENGLISH):\n"
        f" \"Summary\": 2-3 sentence overview in {language} that captures the main purpose of these instructions.\n"
        f" \"SimplifiedInstructions\": array of bullet-point instructions in {language} derived from the text.\n"
        f" \"Importance\": array explaining in {language} why following each instruction is important for health.\n"
        f" \"FollowUpTasks\": array of follow-up tasks or visits in {language}. If none explicitly mentioned, include standard follow-up recommendations relevant to the condition.\n"
        f" \"Medications\": object with two sub-arrays (VALUES IN {language}, KEEP THESE SUB-KEYS IN ENGLISH):\n"
        f"    \"ToTake\": array of medications to take with dosage and purpose in {language}.\n"
        f"    \"ToAvoid\": array of medications and substances to avoid with brief explanation why in {language}.\n"
        f" \"Precautions\": array of warning signs or activities to avoid in {language} based on the condition implied in the instructions.\n"
        f" \"References\": array of brief explanations in {language} supporting the instructions.\n"
        f" \"Disclaimer\": medical disclaimer in {language} stating this is not professional advice.\n\n"
        "STRICT REQUIREMENTS:\n"
        f"1. ALL CONTENT VALUES MUST BE IN {language.upper()}\n"
        f"2. ALL JSON KEYS MUST REMAIN IN ENGLISH EXACTLY AS SHOWN: \"Summary\", \"SimplifiedInstructions\", \"Importance\", \"FollowUpTasks\", \"Medications\", \"ToTake\", \"ToAvoid\", \"Precautions\", \"References\", \"Disclaimer\"\n"
        "3. EVERY section above MUST contain meaningful content - NO empty arrays or objects allowed\n"
        "4. The Medications object MUST contain both ToTake and ToAvoid sub-arrays, each with at least one item\n"
        "5. Clearly distinguish between medications to take versus medications to avoid\n"
        "6. If no medications to take are explicitly mentioned, provide general medication guidance relevant to the condition\n"
        "7. If no medications to avoid are explicitly mentioned, include standard contraindications for the identified condition\n\n"
        f"DOUBLE-CHECK: Before finalizing, verify that your response has:\n"
        f"1. ALL JSON KEYS IN ENGLISH\n"
        f"2. ALL CONTENT VALUES IN {language}\n"
        f"{text}\n"
    )


def simplify_instructions(text: str, language: str = "English"):
    """
    Translate & simplify discharge instructions into patient-friendly language.
    Returns: summary, instructions, importance, follow_up_tasks, medications, precautions, references, disclaimer
    """
    prompt = build_simplify_prompt(text, language)
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
        obj.get("SimplifiedInstructions", []),
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
