import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_AI_KEY")

def simplify_discharge(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4o",
        "messages": [
            {"role": "system", "content": "You simplify discharge instructions to easy patient-friendly English."},
            {"role": "user", "content": text}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        res_json = response.json()
        return res_json["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")
