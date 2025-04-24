import os
import json
import openai
from dotenv import load_dotenv, find_dotenv
from ratelimit import limits, sleep_and_retry

# Load environment variables
_ = load_dotenv(find_dotenv(), override=True)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Rate limit settings
ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 20

@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def _call_openai(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
    """Call OpenAI with automatic rate-limit back-off."""
    try:
        # new v1+ SDK interface
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
    except AttributeError:
        # fallback for older SDKs
        return openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )


def simplify_instructions(text: str, language: str = "English"):
    # Build the enhanced prompt
    prompt = (
        "You are a helpful medical assistant that translates and simplifies discharge instructions.\n"
        f"First, translate **every word** of the following discharge instructions fully into {language}, "
        "making sure **no English remains**. Then, simplify that translated text into clear, patient-friendly "
        "language at approximately a 6th-grade reading level.\n\n"
        "IMPORTANT MEDICAL DISCLAIMER: You will only simplify existing information without adding new medical advice.\n"
        "Do not invent medications - only mention medications explicitly stated in the original text.\n"
        "Each bullet point should be concise (max 20 words) and easy to understand.\n\n"
        "Output *only* a valid JSON object (no extra text) with these keys:\n"
        " \"Summary\": a brief 2-3 sentence overview of what these discharge instructions are about.\n"
        " \"SimplifiedInstructions\": an array of bullet-point sentences explaining what to do.\n"
        " \"Importance\": an array of bullet-point sentences explaining why each instruction matters.\n"
        " \"FollowUpTasks\": an array of bullet-point tasks or visits mentioned in the instructions.\n"
        " \"Medications\": an array of bullet-point medicine-and-dose instructions ONLY if mentioned in the text.\n"
        " \"Precautions\": an array of bullet-point warning signs or activities to avoid.\n"
        " \"References\": an array of bullet-point brief explanations or reasons.\n"
        " \"Disclaimer\": a standard medical disclaimer in the target language stating this is not professional medical advice.\n\n"
        "If certain sections don't apply or aren't mentioned in the original text, include an empty array for that key.\n"
        "If any instructions seem ambiguous or potentially dangerous, add a note in the \"Disclaimer\" section.\n\n"
        f"{text}\n"
    )

    # Call OpenAI with rate limiting
    resp = _call_openai(prompt, model="gpt-3.5-turbo", temperature=0.7)

    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    print("LLM RAW JSON →", raw)

    # Parse JSON
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nRaw output:\n{raw}")

    # Extract fields with defaults
    summary             = obj.get("Summary", "")
    instructions        = obj.get("SimplifiedInstructions", [])
    importance          = obj.get("Importance", [])
    follow_up_tasks     = obj.get("FollowUpTasks", [])
    medications         = obj.get("Medications", [])
    precautions         = obj.get("Precautions", [])
    references          = obj.get("References", [])
    disclaimer          = obj.get("Disclaimer", "")

    return summary, instructions, importance, follow_up_tasks, medications, precautions, references, disclaimer
