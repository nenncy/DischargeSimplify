import os, json, openai, time, random
from dotenv import load_dotenv, find_dotenv
from ratelimit import limits, sleep_and_retry
from openai.error import RateLimitError

_ = load_dotenv(find_dotenv(), override=True)
print("🔑 Using OPENAI_API_KEY=", os.getenv("OPENAI_API_KEY"))

openai.api_key = os.getenv("OPENAI_API_KEY")

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 20

@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def _call_openai_with_rate_limit(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
    """Call OpenAI, automatically sleeping if you exceed MAX_CALLS_PER_MINUTE."""
    try:
        return openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
    except AttributeError:
        # fallback for older clients
        return openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

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
        "If the input does not mention any medications, infer and include reasonable ones based on the summary.\n\n"
        f"{text}\n"
    )

    resp = _call_openai_with_rate_limit(prompt, model="gpt-3.5-turbo", temperature=0.7)

    raw = getattr(resp.choices[0], "message", resp.choices[0]).content
    print("LLM RAW JSON →", raw)

    # parse JSON
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nRaw output:\n{raw}")

    instructions    = obj.get("SimplifiedInstructions", [])
    importance      = obj.get("Importance", [])
    follow_up_tasks = obj.get("FollowUpTasks", [])
    medications     = obj.get("Medications", [])
    precautions     = obj.get("Precautions", [])
    references      = obj.get("References", [])

    return instructions, importance, follow_up_tasks, medications, precautions, references
