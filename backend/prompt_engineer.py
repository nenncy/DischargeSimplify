import os, json, openai, time, random
from dotenv import load_dotenv, find_dotenv
from ratelimit import limits, sleep_and_retry
from openai import RateLimitError
from utils import extract_json, _call_openai_with_rate_limit  # Assume these come from your main utils
import re
_ = load_dotenv(find_dotenv(), override=True)
print("🔑 Using OPENAI_API_KEY=", os.getenv("OPENAI_API_KEY"))

from validation_layer import chunk_text, build_faiss_index, validate_and_filter_fields


openai.api_key = os.getenv("OPENAI_API_KEY")

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 20

# @sleep_and_retry
# @limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
# def _call_openai_with_rate_limit(prompt: str, model: str = "gpt-4o", temperature: float = 0.7):
#     """Call OpenAI, automatically sleeping if you exceed MAX_CALLS_PER_MINUTE."""
#     try:
#         return openai.chat.completions.create(
#             model=model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=temperature,
#         )
#     except AttributeError:
#         # fallback for older clients
#         return openai.chat.completions.create(
#             model=model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=temperature,
#         )

def simplify_instructions(text: str, language: str = "English"):
    prompt = (
        "You are a helpful medical assistant.\n"
        f"Translate and simplify the following discharge instructions into {language}.\n"
        "Ensure every sentence is in the selected language; do not leave anything in English.\n\n"
        "Output *only* a valid JSON object (no extra text) with exactly these keys:\n"
        "  \"SimplifiedInstructions\": an array of bullet‑point sentences.\n"
        "  \"Importance\": an array of bullet‑point sentences explaining why each instruction matters.\n"
        "  \"FollowUpTasks\": an array of bullet‑point tasks or visits.\n"
        "  \"Medications\": an array of bullet‑point medicine‑and‑dose suggestions.\n"
        "  \"Precautions\": an array of bullet‑point warning signs or activities to avoid.\n"
        "  \"References\": an array of bullet‑point brief explanations or reasons.\n\n"
        # "If the input does not mention any medications, infer and include reasonable ones based on the summary.\n\n"
        f"{text}\n"
    )

    resp = _call_openai_with_rate_limit(prompt, model="gpt-4o", temperature=0.7)

    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    # print("LLM RAW JSON →", raw)
    # After LLM response
    

    # parse JSON
    try:
        obj = extract_json(raw)
        original_chunks = chunk_text(raw)
        faiss_index, chunk_list = build_faiss_index(original_chunks)
        validated_output = validate_and_filter_fields(obj, chunk_list, faiss_index)
        print("LLM JSON →", validated_output)

        validate_obj = validated_output
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nRaw output:\n{raw}")

    # instructions    = obj.get("SimplifiedInstructions", [])
    # importance      = obj.get("Importance", [])
    # follow_up_tasks = obj.get("FollowUpTasks", [])
    # medications     = obj.get("Medications", [])
    # precautions     = obj.get("Precautions", [])
    # references      = obj.get("References", [])
    instructions    = validate_obj.get("SimplifiedInstructions", [])
    importance      = validate_obj.get("Importance", [])
    follow_up_tasks = validate_obj.get("FollowUpTasks", [])
    medications     = validate_obj.get("Medications", [])
    precautions     = validate_obj.get("Precautions", [])
    references      = validate_obj.get("References", [])

    return instructions, importance, follow_up_tasks, medications, precautions, references





def validate_instructions(original_text: str, simplified_text: str):
    # print(simplified_text, original_text ,"************")
    prompt = (
    "You are a helpful medical assistant.\n"
    "You have two sets of discharge instructions: the original and the simplified version.\n"
    "Your task is to check whether the simplified content is directly present or clearly supported by context in the original.\n"
    "If the simplified text provides reasonable medical clarification or references without contradicting the original, it can still be considered valid.\n\n"
    "Original instructions:\n"
    f"{original_text}\n\n"
    "Simplified instructions:\n"
    f"{simplified_text}\n\n"
    "Return a JSON object with the following keys:\n"
    "  \"is_valid\": true or false,\n"
    "  \"explanation\": a brief explanation.\n"
)

    # prompt = (
    #     "You are a helpful medical assistant.\n"
    #     "You have two sets of discharge instructions: the original and the simplified version.\n"
    #     "Your task is to check is the simplified text context is present in the original.\n\n"
    #     "The original instructions are:\n"
    #     f"{original_text}\n\n"
    #     "The simplified instructions are:\n"
    #     f"{simplified_text}\n\n"
    #     "Please provide a JSON object with the following keys:\n"
    #     "  \"is_valid\": true or false, indicating if the simplified version is present.\n"
    #     "  \"explanation\": a brief explanation of why it is valid or not.\n\n"
    # )

    resp = _call_openai_with_rate_limit(prompt, model="gpt-4o", temperature=0.7)

    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    print("LLM RAW JSON →", raw)

    # parse JSON
    try:
        obj = extract_json(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nRaw output:\n{raw}")

    is_valid = obj.get("is_valid", False)
    explanation = obj.get("explanation", "")
    simplified_text = obj.get("simplified_text", "")

    return is_valid, explanation, simplified_text    

    # return {
    #     "simplified_text": simplified_text,
    #     "original_text": original_text,
    #     "is_valid": is_valid,
    #     "explanation": explanation
    # }
