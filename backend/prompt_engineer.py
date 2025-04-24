import os, json, openai, time, random
from dotenv import load_dotenv, find_dotenv
from ratelimit import limits, sleep_and_retry
#from openai.error import RateLimitError

_ = load_dotenv(find_dotenv(), override=True)
print("🔑 Using OPENAI_API_KEY=", os.getenv("OPENAI_API_KEY"))

openai.api_key = os.getenv("OPENAI_API_KEY")

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 20

@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def _call_openai_with_rate_limit(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.0):
    """Call OpenAI, automatically sleeping if you exceed MAX_CALLS_PER_MINUTE."""
    return openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    
def generate_concise_summary(text: str, language: str = "English") -> str:
    if language.lower() == "english":
        prompt1 = (
            "You are a professional medical summarizer.\n"
            "Simplify the following discharge instructions into a single concise paragraph.  \n"
            "Include all essential details including information related to the patient especially the diagnosis and the reason in patient-friendly overview.\n"
            "Ensure every sentence is in English; do not use any other language.\n\n"
            "Output exactly one short paragraph (no bullet points or sections):\n\n"
            f"\"\"\"{text}\"\"\""
        )
    else:
        prompt1 = (
            "You are a professional medical translator and summarizer.\n"
            f"Translate the following discharge instructions fully into {language}, "
            "and then simplify them into a single concise paragraph in that same language.  \n"
            "Include all essential details including information related to the patient especially the diagnosis and the reason in patient-friendly overview.\n"
            "Ensure every sentence is in the selected language; do not leave anything in English.\n\n"
            "Output exactly one short paragraph (no bullet points or sections):\n\n"
            f"\"\"\"{text}\"\"\""
        )
    resp1 = _call_openai_with_rate_limit(prompt1, model="gpt-3.5-turbo", temperature=0)
    paragraph = resp1.choices[0].message.content.strip()
    paragraph = paragraph.strip().strip('```"')
    if not paragraph:
        raise RuntimeError("Received empty summary from LLM.")
    print("LLM Concise Summary:", paragraph)
    return paragraph 

def simplify_instructions(text: str, language: str = "English", reading_level: int = 6):
    prompt2 = (
        "You are a helpful medical assistant.\n"
        f"Translate and simplify the following discharge instructions into {language} at {reading_level}th grade level.\n"
        "Ensure every sentence is in the selected language; do not leave anything in English.\n\n"
        "Output *only* a valid JSON object (no extra text) with exactly these keys:\n"
        "  \"SimplifiedInstructions\": an array of bullet-point sentences.\n"
        "  \"Importance\": an array of bullet-point sentences explaining why each instruction matters.\n"
        "  \"FollowUpTasks\": an array of bullet-point tasks or visits.\n"
        "  \"Medications\": an array of bullet-point medicine-and-dose suggestions.\n"
        "  \"Precautions\": an array of bullet-point warning signs or activities to avoid.\n"
        "  \"References\": an array of bullet-point brief explanations or reasons.\n\n"
        "If the input does not mention any medications, infer and include reasonable ones based on the summary.\n\n"
        "Make sure under each heading, provide bullet points where:\n"
        "  • Each bullet is a single, complete sentence ending with a period.\n"
        "  • Do NOT split one idea across multiple bullets or lines.\n\n"
        f"Now simplify:\n\"\"\"{text}\"\"\""
    )

    resp2 = _call_openai_with_rate_limit(prompt2, model="gpt-3.5-turbo", temperature=0)
    raw = getattr(resp2.choices[0], "message", resp2.choices[0]).content
    print("LLM RAW JSON:", raw)

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
