import os, json, requests, openai
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv(), override=True)
API_KEY = os.getenv("OPENAI_API_KEY")
print("🔑 Using OPENAI_API_KEY=", os.getenv("OPENAI_API_KEY"))
BACKEND_URL  = os.getenv("BACKEND_URL")

# 2) Build the Assistants.create request
URL = "https://api.openai.com/v1/assistants"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type":  "application/json",
    "OpenAI-Beta":   "assistants=v2"
}

# 3) Payload: minimal v1 schema
payload = {
    "name":         "Discharge Helper",
    "description":  "Answers follow-up questions STRICTLY from the user’s own simplified discharge instructions.",
    "instructions": (
        "You are the Discharge-Helper Assistant. You MUST answer questions *only* from the provided 'context' "
        "of simplified instructions. If the answer is not in that context, reply “I’m sorry, I don’t have that information.”"
    ),
    "model":        "gpt-3.5-turbo"
}

# 4) Create the assistant
resp = requests.post(URL, headers=HEADERS, json=payload)
resp.raise_for_status()

assistant = resp.json()
assistant_id = assistant["id"]
print("✅ Created assistant:", assistant_id)

