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


def simplify_instructions(text: str, language: str = "English"):
    """
    Translate & simplify discharge instructions into patient-friendly language.
    Returns: summary, instructions, importance, follow_up_tasks, medications, precautions, references, disclaimer
    """
    prompt = (
        "You are a helpful medical assistant that translates and simplifies discharge instructions.\n"
        f"First, translate **every word** of the following discharge instructions fully into {language}, making sure **no English remains**. "
        "Then, simplify that translated text into clear, patient-friendly language at approximately a 6th-grade reading level.\n\n"
        "IMPORTANT MEDICAL DISCLAIMER: Only simplify existing information; do not add new medical advice.\n"
        "Do not invent medications — only mention those explicitly stated. Each bullet point max 20 words.\n\n"
        "Output only a valid JSON object with keys:\n"
        "  \"Summary\": 2-3 sentence overview.\n"
        "  \"SimplifiedInstructions\": array of bullet-point instructions.\n"
        "  \"Importance\": array explaining why each matters.\n"
        "  \"FollowUpTasks\": array of follow-up tasks or visits.\n"
        "  \"Medications\": array of medicine-dose info if mentioned.\n"
        "  \"Precautions\": array of warning signs or activities to avoid.\n"
        "  \"References\": array of brief explanations or reasons.\n"
        "  \"Disclaimer\": medical disclaimer stating this is not professional advice.\n\n"
        "If a section does not apply, return an empty array for that key.\n"
        f"{text}\n"
    )

    resp = _call_openai(prompt)
    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    print("LLM RAW JSON →", raw)

    try:
        obj = extract_json(raw)
        original_chunks = chunk_text(raw)
        faiss_index, chunk_list = build_faiss_index(original_chunks)
        validated_output = validate_and_filter_fields(obj, chunk_list, faiss_index)
        print("LLM JSON →", validated_output , obj)
        validate_obj = validated_output

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nRaw output:\n{raw}")

    # Return raw parsed JSON fields (no FAISS filtering here)
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
