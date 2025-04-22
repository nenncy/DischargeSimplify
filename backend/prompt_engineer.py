# backend/prompt_engineer.py

import os, json, openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def simplify_instructions(text: str, language: str = "English"):
    prompt = (
        "You are a helpful medical assistant.\n"
        f"Translate and simplify the following discharge instructions into {language}.\n"
        "Ensure that **every piece of text** (Summary, Precautions, Medications values) is written in "
        f"{language}, and do **not** leave anything in English.\n\n"
        "Then output **only** a JSON object (no extra text) with exactly these keys:\n"
        "  \"Summary\": a short description of the condition\n"
        "  \"Precautions\": an array of warning strings\n"
        "  \"Medications\": an array of medicine-and-dose suggestions\n\n"
        # Keep meds inference instruction
        "Always infer and include reasonable medications based on the summary.\n\n"
        f"{text}\n"
    )

    # send to OpenAI (v1+ or fallback)
    try:
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
        )
    except AttributeError:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
        )

    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    print("LLM RAW JSON →", raw)      # for your logs

    # parse JSON
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\n{raw}")

    summary     = obj.get("Summary", "")
    precautions = obj.get("Precautions", [])
    medications = obj.get("Medications", [])

    # re‑assemble summary + precautions into your one text‐area
    simplified = f"Summary: {summary}\n\nPrecautions:\n" + "\n".join(precautions)
    return simplified, precautions, medications